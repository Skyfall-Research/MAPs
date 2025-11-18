from enum import IntEnum
from pydantic import BaseModel, Field, RootModel, field_validator, ConfigDict
from typing import Any, Optional, Self, List, Dict, Tuple, Union
from contextvars import ContextVar
from contextlib import contextmanager
import copy
import yaml

import importlib.resources
MODULE_PATH = importlib.resources.files(__package__)
GUEST_ENUMS = yaml.safe_load(open(MODULE_PATH/'../../shared/guest_enums.yaml'))

from map_py.eval.utils import GameState

class ParkDataGranularity(IntEnum):
    """Enumeration for the granularity level of park observation data.
    
    Controls the level of detail included in observations. Higher granularity includes
    more detailed information (individual items, coordinates, etc.), while lower granularity
    provides aggregated summaries (totals, averages, etc.).

    Generally speaking, HIGH should always be used.
    
    Attributes:
        HIGH: Detailed observations including individual items, coordinates, and
            per-entity information. Use this by default.
        LOW: Aggregated/summary observations including totals, averages, and high-level
            statistics. Use this for efficient processing and reduced data size.
    """
    HIGH=0    # More detailed observations (individual items, coordinates, etc.)
    LOW=1    # Aggregated/summary observations (totals, averages, etc.)

    def __str__(self):
        return self.name

class ParkObservabilityMode(IntEnum):
    """Enumeration for the observability mode of park observations.
    
    Controls what information is visible in observations. Normal mode provides only
    information that would be realistically observable, while oracle mode includes
    additional information that would not normally be visible.
    
    Attributes:
        NORMAL: Standard observability mode with only realistically observable information.
            Fields marked with this mode or higher will be included.
        ORACLE: Enhanced observability mode with additional information beyond normal
            observation capabilities. Includes all fields marked with NORMAL or ORACLE.
    """
    NORMAL=0
    ORACLE=1 # oracle is more observations

    def __str__(self):
        return self.name

data_level_context = ContextVar('data_level', default=ParkDataGranularity.HIGH)
observability_mode_context = ContextVar('observability_mode', default=ParkObservabilityMode.ORACLE)

@contextmanager
def park_observability_context(data_level: ParkDataGranularity, observability_mode: ParkObservabilityMode):
    """Context manager to safely set and reset observability context variables.
    
    Temporarily sets the data level and observability mode context variables for the
    duration of the context. These context variables are used by ModelWithLevels
    and RootModelWithLevels to filter fields based on the current settings.
    
    Args:
        data_level: The data granularity level to use within this context.
        observability_mode: The observability mode to use within this context.
    
    Yields:
        None. The context variables are active during the yield.
    
    Example:
        ```python
        with park_observability_context(ParkDataGranularity.LOW, ParkObservabilityMode.NORMAL):
            obs = FullParkObs(...)  # Fields will be filtered based on LOW/NORMAL settings
        ```
    """
    token_data = data_level_context.set(data_level)
    token_obs = observability_mode_context.set(observability_mode)
    try:
        yield
    finally:
        data_level_context.reset(token_data)
        observability_mode_context.reset(token_obs)

# A cleaner Field factory function.
def FieldWithMode(
    *, # make data_level and observability_mode keyword-only for clarity
    data_level: ParkDataGranularity, 
    observability_mode: ParkObservabilityMode, 
    **kwargs
):
    """Attaches data level and observability mode metadata to a Pydantic Field."""
    # Since these fields can be filtered out, they must have a default value.
    # We default to None unless another default is provided.
    if 'default' not in kwargs:
        kwargs['default'] = None
        
    json_schema_extra = kwargs.get('json_schema_extra', {})
    json_schema_extra['data_level'] = data_level
    json_schema_extra['observability_mode'] = observability_mode
    kwargs['json_schema_extra'] = json_schema_extra
    
    return Field(**kwargs)

def _should_filter_field(field_data_level: Optional[ParkDataGranularity], field_obs_mode: Optional[ParkObservabilityMode]) -> bool:
    """Helper function to determine if a field should be filtered based on current context."""
    current_data_level = data_level_context.get()
    current_observability_mode = observability_mode_context.get()
    
    return (field_data_level is not None and field_data_level < current_data_level) or \
           (field_obs_mode is not None and field_obs_mode > current_observability_mode)

class ModelWithLevels(BaseModel):
    """Base class for Pydantic models that support context-based field filtering.
    
    This class extends Pydantic's BaseModel to automatically filter fields based on
    the current data_level and observability_mode context variables. Fields marked
    with FieldWithMode() are filtered during initialization if they don't match
    the current context settings.
    
    Fields are filtered by setting them to None if:
    - The field's data_level is higher than the current context, OR
    - The field's observability_mode is higher than the current context.
    
    All models that need granularity/observability filtering should inherit from
    this class rather than BaseModel directly.
    """
    model_config = ConfigDict(frozen=False)
    
    def __init__(self, **data):
        # Filter fields before calling parent constructor
        filtered_data = {}
        for field_name, field_value in data.items():
            if field_value is None:
                filtered_data[field_name] = None
                continue
                
            field_info = self.__class__.model_fields.get(field_name)
            if not field_info or not field_info.json_schema_extra:
                filtered_data[field_name] = field_value
                continue
                
            field_data_level = field_info.json_schema_extra.get('data_level')
            field_obs_mode = field_info.json_schema_extra.get('observability_mode')
            
            if _should_filter_field(field_data_level, field_obs_mode):
                filtered_data[field_name] = None
            else:
                filtered_data[field_name] = field_value
        
        super().__init__(**filtered_data)

class RootModelWithLevels(RootModel):
    """Base class for Pydantic RootModels that support context-based field filtering.
    
    This class extends Pydantic's RootModel to automatically filter the root field
    based on the current data_level and observability_mode context variables.
    The root field is filtered during initialization if it doesn't match the
    current context settings.
    
    Similar to ModelWithLevels but designed for models that use a single root value
    rather than multiple named fields.
    """
    model_config = ConfigDict(frozen=False)
    
    def __init__(self, **data):
        # Filter root field before calling parent constructor
        if 'root' in data:
            field_info = self.__class__.model_fields.get('root')
            if field_info and field_info.json_schema_extra:
                field_data_level = field_info.json_schema_extra.get('data_level')
                field_obs_mode = field_info.json_schema_extra.get('observability_mode')
                
                if _should_filter_field(field_data_level, field_obs_mode):
                    data['root'] = None
        
        super().__init__(**data)

## --- 2. UPDATED MODEL DEFINITIONS ---
# All models now inherit from ModelWithLevels or RootModelWithLevels.
# All filterable fields are now explicitly Optional.

class GuestStats(ModelWithLevels): 
    """Aggregate statistics about guests for a given day.
    
    Provides up-to-date aggregate information about all guests in the park.
    Updated every day and includes only information that would be visible in normal
    observability mode (not oracle-level details).
    
    Differs from GuestSurveyResult in that:
    - This provides aggregate statistics for all guests
    - GuestSurveyResult provides information about specific individual guests
    - This is updated automatically every day
    - GuestSurveyResult is only updated when guests are surveyed
    """
    total_guests: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    avg_money_spent: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    avg_time_in_park: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    avg_rides_visited: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    avg_food_shops_visited: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    avg_drink_shops_visited: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    avg_specialty_shops_visited: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)

class GuestSurveyResult(ModelWithLevels):
    """Information about a specific guest retrieved from guest surveys.
    
    Provides detailed information about an individual guest's experience, including
    their state at exit, preferences, and spending patterns. This information is
    only available when guests are explicitly surveyed using the survey_guests action.
    
    Differs from GuestStats in that:
    - This provides information about specific individual guests
    - GuestStats provides aggregate statistics for all guests
    - This is only updated when guests are surveyed
    - GuestStats is updated automatically every day
    """
    happiness_at_exit: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    hunger_at_exit: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    thirst_at_exit: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    remaining_energy: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    remaining_money: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    percent_of_money_spent: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    reason_for_exit: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    preference: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)

class GuestSurveyResults(ModelWithLevels):
    """Container for multiple guest survey results.
    
    Holds a list of individual guest survey results along with metadata about
    when the surveys were conducted.
    """
    age_of_results: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    list_of_results: Optional[List[GuestSurveyResult]] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)

class Shop(ModelWithLevels):
    """Information about a single shop in the park.
    
    Contains detailed information about shop location, pricing, inventory, operations,
    and performance metrics. All fields are at HIGH data granularity and NORMAL
    observability mode.
    """
    subtype: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    subclass: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    x: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    y: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    item_price: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    item_cost: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    operating_cost: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    uptime: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    number_of_restocks: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    order_quantity: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    inventory: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    revenue_generated: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    cleanliness: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    guests_served: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    out_of_service: Optional[bool] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)

class Shops(ModelWithLevels):
    """Aggregate information about all shops in the park.
    
    Contains both summary statistics (LOW granularity) and a detailed list of
    individual shops (HIGH granularity).
    """
    total_shops: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_revenue_generated: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_operating_cost: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    min_uptime: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    shop_list: Optional[List[Shop]] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)

class Ride(ModelWithLevels):
    """Information about a single ride in the park.
    
    Contains detailed information about ride location, pricing, operations, capacity,
    excitement/intensity ratings, and performance metrics. All fields are at HIGH
    data granularity and NORMAL observability mode.
    """
    subtype: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    subclass: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    x: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    y: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    out_of_service: Optional[bool] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    uptime: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    cleanliness: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    ticket_price: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    operating_cost: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    revenue_generated: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    capacity: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    intensity: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    excitement: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    guests_entertained: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    times_operated: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    cost_per_operation: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    avg_wait_time: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    avg_guests_per_operation: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    breakdown_rate: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)

class Rides(ModelWithLevels):
    """Aggregate information about all rides in the park.
    
    Contains both summary statistics (LOW granularity) and a detailed list of
    individual rides (HIGH granularity).
    """
    total_rides: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    min_uptime: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_operating_cost: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_revenue_generated: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_excitement: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    avg_intensity: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_capacity: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    ride_list: Optional[List[Ride]] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)

class Employee(ModelWithLevels):
    """Information about a single employee (staff member) in the park.
    
    Contains detailed information about employee location, type, salary, performance
    metrics, and operational costs. All fields are at HIGH data granularity and
    NORMAL observability mode.
    """
    subtype: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    subclass: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    x: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    y: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    salary: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    operating_cost: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    success_metric: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    success_metric_value: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    tiles_traversed: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)

class Staff(ModelWithLevels):
    """Aggregate information about all staff (employees) in the park.
    
    Contains both summary statistics (LOW granularity) and a detailed list of
    individual employees (HIGH granularity).
    """
    total_janitors: Optional[List[int]] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_mechanics: Optional[List[int]] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_specialists: Optional[List[int]] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_salary_paid: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    total_operating_cost: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    staff_list: Optional[List[Employee]] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)

class Path(ModelWithLevels):
    """Information about a single path tile in the park.
    
    Contains location and cleanliness information for individual path tiles.
    All fields are at HIGH data granularity and NORMAL observability mode.
    """
    x: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    y: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    cleanliness: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)

class Water(ModelWithLevels):
    """Information about a single water tile in the park.
    
    Contains location information for individual water tiles.
    All fields are at HIGH data granularity and NORMAL observability mode.
    """
    x: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    y: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)

class FullParkObs(ModelWithLevels, GameState):
    """Complete park observation containing all available information about the park state.
    
    This is the main observation model returned by the environment. It contains
    comprehensive information about the park including:
    - Park state (money, revenue, expenses, rating, etc.)
    - Guest statistics and survey results
    - Ride and shop information (both aggregate and detailed)
    - Staff information
    - Research status
    - Park layout (entrance, exit, paths, water tiles)
    
    Fields are filtered based on the data_level and observability_mode context
    when the observation is created. Use park_observability_context() to control
    what information is included.
    """
    parkId: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    step: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    horizon: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    value: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    money: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    revenue: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL) # stochastic
    expenses: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL) 
    profit: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    park_rating: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL) # "stochastic"
    guests: Optional[GuestStats] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    guest_survey_results: Optional[GuestSurveyResults] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    rides: Optional[Rides] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    shops: Optional[Shops] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    staff: Optional[Staff] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    research_speed: Optional[str] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    research_topics: Optional[List[str]] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    research_operating_cost: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    available_entities: Optional[Dict[str, List[str]]] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    fast_days_since_last_new_entity: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    medium_days_since_last_new_entity: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    slow_days_since_last_new_entity: Optional[int] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    new_entity_available: Optional[bool] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    entrance: Optional[Tuple[int, int]] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    exit: Optional[Tuple[int, int]] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL)
    paths: Optional[List[Path]] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    waters: Optional[List[Water]] = FieldWithMode(data_level=ParkDataGranularity.HIGH, observability_mode=ParkObservabilityMode.NORMAL)
    min_cleanliness: Optional[float] = FieldWithMode(data_level=ParkDataGranularity.LOW, observability_mode=ParkObservabilityMode.NORMAL) 


    @classmethod
    def to_level(cls, state: 'FullParkObs', data_level: ParkDataGranularity, observability_mode: ParkObservabilityMode) -> 'FullParkObs':
        """Create a new FullParkObs with reduced data level and/or observability mode.
        
        Creates a copy of the observation with fields filtered according to the
        specified data_level and observability_mode. This is useful for converting
        a HIGH/ORACLE observation to a LOW/NORMAL observation.
        
        Warning:
            This method only works to **reduce** the data level or observability mode.
            It cannot restore information that was already filtered out. To increase
            the data level or observability mode, you need to recreate the observation
            from the raw state with the desired settings.
        
        Args:
            state: The FullParkObs instance to convert.
            data_level: The target data granularity level (must be >= current level).
            observability_mode: The target observability mode (must be <= current mode).
        
        Returns:
            A new FullParkObs instance with fields filtered according to the
            specified data_level and observability_mode.
        """
        with park_observability_context(data_level, observability_mode):
            return cls(**state.model_dump())
        
## --- 3. REVISED `format_state` FUNCTION ---
def format_pydantic_observation(state: dict, observability_mode: ParkObservabilityMode = ParkObservabilityMode.ORACLE, 
                                 data_level: ParkDataGranularity = ParkDataGranularity.HIGH, 
                                 as_dict: bool = False) -> Union[FullParkObs, dict]:
    """Format raw park state dictionary into a structured Pydantic observation.
    
    Converts a raw state dictionary (from the backend) into a FullParkObs model,
    filtering fields based on the specified observability mode and data level.
    The function processes guest data, staff data, rides, shops, terrain, and
    other park information into structured models.
    
    Args:
        state: Raw state dictionary from the backend containing park information.
        observability_mode: The observability mode to use for field filtering.
            Defaults to ORACLE (most information).
        data_level: The data granularity level to use for field filtering.
            Defaults to HIGH (most detailed).
        as_dict: If True, returns a dictionary instead of a FullParkObs model.
            The dictionary excludes None values for cleaner output.
    
    Returns:
        A FullParkObs instance if as_dict is False, or a dictionary representation
        if as_dict is True. Fields are filtered according to the specified
        observability_mode and data_level.
    """
    guest_data, staff_data = format_people(state)
    ride_data, shop_data, cleanliness = format_attractions(state)

    state_obs_model = None

    # round guest_survey_results
    for result in state['guest_survey_results']['list_of_results']:
        result['reason_for_exit'] = GUEST_ENUMS['exit_reasons'][result['reason_for_exit_id']]["description"]
        result['preference'] = GUEST_ENUMS['preferences'][result['preference_id']]["description"]
        for k, v in result.items():
            if isinstance(v, float):
                result[k] = round(v, 2)

    paths = []
    waters = []
    for terrain in state['terrain']:
        if terrain['type'] == 'path':
            paths.append(terrain)
            cleanliness.append(terrain['cleanliness'])
        elif terrain['type'] == 'water':
            waters.append(terrain)
        
    min_cleanliness = round(min(cleanliness), 2)    

    # Use the context manager to set the settings before creating the Pydantic object
    with park_observability_context(data_level, observability_mode): 
        state_obs_model = FullParkObs(
            parkId=state['state']['parkId'],
            step=state['state']['step'],
            horizon=state['state']['horizon'],
            value=state['state']['value'],
            money=state['state']['money'],
            revenue=state['state']['revenue'],
            expenses=state['state']['expenses'],
            profit=state['state']['revenue'] - state['state']['expenses'],
            park_rating=round(state['state']['park_rating'], 2),
            guests=guest_data,
            guest_survey_results=state['guest_survey_results'],
            rides=ride_data,
            shops=shop_data,
            staff=staff_data,
            research_speed=state['state']['research_speed'],
            research_topics=state['state']['research_topics'],
            research_operating_cost=state['state']['research_operating_cost'],
            available_entities=state['state']['available_entities'],
            fast_days_since_last_new_entity=state['state']['fast_days_since_last_new_entity'],
            medium_days_since_last_new_entity=state['state']['medium_days_since_last_new_entity'],
            slow_days_since_last_new_entity=state['state']['slow_days_since_last_new_entity'],
            new_entity_available=state['state']['new_entity_available'],
            #new_attraction_available=state['state']['new_entity_available'],
            min_cleanliness=min_cleanliness,
            entrance=(state['entrance']['x'], state['entrance']['y']),
            exit=(state['exit']['x'], state['exit']['y']),
            paths=paths,
            waters=waters
        )
    
    if as_dict:
        # Exclude None values for a cleaner output dictionary
        return state_obs_model.model_dump(exclude_none=True)

    return state_obs_model

def format_people(state: dict) -> Tuple[dict, dict]:
    """Format guest and staff data from raw state dictionary.
    
    Processes guest statistics and staff information from the raw state,
    organizing them into structured dictionaries suitable for creating
    GuestStats and Staff models.
    
    Args:
        state: Raw state dictionary from the backend.
    
    Returns:
        A tuple containing:
            - guest_data: Dictionary with guest statistics (total_guests,
              avg_money_spent, avg_time_in_park, etc.)
            - staff_data: Dictionary with staff information (total counts by type,
              salary information, staff_list, etc.)
    
    Raises:
        ValueError: If guestStats is not found in the state dictionary.
    """
    # Use guestStats from the state if available, otherwise compute from individual guests
    if 'guestStats' in state:
        guest_data = {
            'total_guests': state['guestStats']['total_guests'],
            'avg_money_spent': state['guestStats']['avg_money_spent'],
            'avg_time_in_park': state['guestStats']['avg_steps_taken'],
            'avg_rides_visited': state['guestStats']['avg_rides_visited'],
            'avg_food_shops_visited': state['guestStats']['avg_food_shops_visited'],
            'avg_drink_shops_visited': state['guestStats']['avg_drink_shops_visited'],
            'avg_specialty_shops_visited': state['guestStats']['avg_specialty_shops_visited']
        }
    else:
        # Fallback to computing from individual guests (for backward compatibility)
        raise ValueError("Guest stats not found in state")

    # Build staff data
    staff_data = {
        'total_janitors': [0, 0, 0, 0],
        'total_mechanics': [0, 0, 0, 0],
        'total_specialists': [0, 0, 0, 0],
        'total_salary_paid': 0,
        'total_operating_cost': 0,
        'staff_list': [],
    }
    idx = {'yellow': 0, 'blue': 1, 'green': 2, 'red': 3}
    
    staff_data['total_salary_paid'] = state['state']['total_salary_paid']

    for staff_member in state['staff']:
        staff_data['total_operating_cost'] += staff_member['operating_cost']
        staff_data['staff_list'].append(staff_member)
        staff_data[f'total_{staff_member["subtype"]}s'][idx[staff_member["subclass"]]] += 1
        
    return guest_data, staff_data

def format_attractions(state: dict) -> Tuple[dict, dict, List[float]]:
    """Format ride and shop data from raw state dictionary.
    
    Processes ride and shop information from the raw state, calculating
    aggregate statistics and organizing them into structured dictionaries.
    Also collects cleanliness values from all attractions for minimum calculation.
    
    Args:
        state: Raw state dictionary from the backend.
    
    Returns:
        A tuple containing:
            - ride_data: Dictionary with ride statistics (total_rides, min_uptime,
              total_operating_cost, total_revenue_generated, ride_list, etc.)
            - shop_data: Dictionary with shop statistics (total_shops,
              total_operating_cost, total_revenue_generated, min_uptime, shop_list, etc.)
            - cleanliness: List of all cleanliness values from rides, shops, and paths
              (used for calculating minimum park cleanliness)
    """
    cleanliness = []

    # Build ride data
    ride_data = {
        'total_rides': 0,
        'min_uptime': [],
        'total_operating_cost': 0,
        'total_revenue_generated': 0,
        'total_excitement': state['state']['park_excitement'],
        'avg_intensity': 0.0,
        'total_capacity': 0,
        'ride_list': []
    }
    
    # Calculate ride totals
    for ride in state['rides']:
        ride_data['total_rides'] += 1
        ride_data['min_uptime'].append(round(float(ride['uptime']), 2))
        ride_data['total_operating_cost'] += ride['operating_cost']
        ride_data['total_revenue_generated'] += ride['revenue_generated']
        ride_data['total_capacity'] += ride['capacity']
        ride_data['avg_intensity'] += round(float(ride['intensity']), 2)
        ride_data['ride_list'].append(ride)
        cleanliness.append(ride['cleanliness'])

    # Calculate ride averages
    if ride_data['total_rides'] > 0:
        ride_data['min_uptime'] = min(ride_data['min_uptime'])
        ride_data['avg_intensity'] = round(ride_data['avg_intensity'] / ride_data['total_rides'], 2)
    else:
        ride_data['min_uptime'] = 1.0

    # Build shop data
    shop_data = {
        'total_shops': 0,
        'total_operating_cost': 0,
        'total_revenue_generated': 0,
        'min_uptime': [],
        'shop_list': []
    }
    
    for shop in state['shops']:
        shop_data['total_shops'] += 1
        assert shop['operating_cost'] is not None, shop
        shop_data['total_operating_cost'] += shop['operating_cost']
        shop_data['total_revenue_generated'] += shop['revenue_generated']
        shop_data['min_uptime'].append(round(float(shop['uptime']), 2))
        shop_data['shop_list'].append(shop)
        cleanliness.append(shop['cleanliness'])

    if shop_data['total_shops'] > 0:
        shop_data['min_uptime'] = min(shop_data['min_uptime'])
    else:
        shop_data['min_uptime'] = 1.0

    return ride_data, shop_data, cleanliness
