from __future__ import annotations
from enum import Enum
from typing import Optional, Iterator
import copy 
from collections import defaultdict
import numpy as np
from llm_model_cost import ModelCost

class CannotEstimateCostError(Exception):
    """Exception raised when resource cost cannot be estimated.
    
    This exception is raised when attempting to calculate USD costs for resources
    (e.g., LLM tokens) but the necessary information (model registration, cost data)
    is not available.
    """
    def __init__(self, error_message: str) -> None:
        """Initialize the exception with an error message.

        Args:
            error_message: A descriptive error message explaining why the cost cannot be estimated.
        """
        super().__init__(error_message)

class Resource(Enum):
    """Enumeration representing types of high-level resources being consumed.
    
    This enum is used within the ResourceCost class, where a string label (e.g., model name)
    is combined with the Resource type. For example, Resource.TOKENS_IN is combined 
    with 'gpt-4o-mini' to track input tokens for that specific model.

    This class can be subclassed to record other types of resources
    (e.g., cloud resource usage, API calls, etc.).
    
    Attributes:
        TOKENS_IN: Represents input tokens consumed (e.g., prompt tokens).
        TOKENS_OUT: Represents output tokens consumed (e.g., completion tokens).
    """
    # LLM input/output tokens
    TOKENS_IN = 1
    TOKENS_OUT = 2

class ResourceCost:
    """Class for representing and tracking resource costs, primarily LLM input and output tokens.
    
    This class tracks resource consumption (e.g., token usage) for models and can convert
    these to USD costs. It supports both registered models (via ModelCost library) and
    custom model registrations.
    
    This class should be subclassed with to_usd() updated if the model being evaluated
    uses significant non-LLM resources (e.g., cloud compute, API calls, storage).

    Attributes:
        _custom_models: Class-level dictionary storing custom model cost registrations.
            Maps model names to dictionaries of Resource -> cost per unit.
    """
    _custom_models: dict[str, dict[Resource, float]] = {}
    
    def __init__(self, model: str | None = None, costs: dict[Resource, float] | None = None) -> None:
        """Initialize a ResourceCost instance.

        Args:
            model: Name of the model/resource (e.g., 'gpt-4o-mini'), or None if there is no cost.
                The model must be registered (either via register_custom_model() or available
                in the ModelCost library).
            costs: Dictionary mapping Resource types to their consumption values (e.g., 
                {Resource.TOKENS_IN: 1000.0, Resource.TOKENS_OUT: 500.0}). Defaults to None,
                which creates an empty cost dictionary (i.e. no resources used).

        Raises:
            CannotEstimateCostError: If model is provided but not registered.
        """
        if model is not None and not ResourceCost.is_registered(model):
            raise CannotEstimateCostError(f"Model {model} is unknown, please register model with ResourceCost.register_custom_model or subclass ResourceCost to implement USD cost estimation")

        super().__init__()
        if costs is None:
            costs = {}

        self._resources = {}
        if model:
            self._resources = {model: costs}
        else:
            assert costs == {}
    
    @staticmethod
    def register_custom_model(model_name: str, input_cost: float, output_cost: float) -> None:
        """Register a custom model's token costs, overriding the default cost calculation library.

        This method allows you to specify custom pricing for models that may not be available
        in the ModelCost library or to override existing pricing. Once registered, this model
        will use the custom costs instead of the library's default calculations.

        Note:
            - This registration is shared among all ResourceCost instances (class-level).
            - Custom registrations take precedence over the default library's calculations.
            - Costs should be provided per 1M tokens, but are stored internally as per-token costs.

        Args:
            model_name: The name/identifier of the model (e.g., 'custom-model-v1').
            input_cost: Cost per 1 million input tokens (will be internally converted to per-token cost).
            output_cost: Cost per 1 million output tokens (will be internally converted to per-token cost).
        """
        ResourceCost._custom_models[model_name] = {Resource.TOKENS_IN: input_cost/10**6, Resource.TOKENS_OUT: output_cost/10**6}

    @staticmethod
    def is_registered(model_name: str) -> bool:
        """Check whether cost calculation is available for a given model.

        A model is considered registered if it has been registered via register_custom_model()
        or if it is available in the ModelCost library.

        Args:
            model_name: The name/identifier of the model to check.

        Returns:
            True if the model is registered and cost can be calculated, False otherwise.
        """
        return model_name in ResourceCost._custom_models or model_name in ModelCost.list_models()

    def to_usd(self, raise_on_uncalculable: bool = False) -> Optional[float]:
        """Convert this resource cost to USD.

        Calculates the total USD cost by summing costs for all registered models and resource types.
        For LLM tokens, uses either custom model registrations or the ModelCost library.

        Args:
            raise_on_uncalculable: If True, raises CannotEstimateCostError when cost cannot be
                calculated. If False, returns None in such cases.

        Returns:
            The total cost in USD, or None if the cost cannot be calculated and 
            raise_on_uncalculable is False.

        Raises:
            CannotEstimateCostError: If raise_on_uncalculable is True and there is no way to
                calculate the cost (e.g., unregistered model or unknown resource type).
        """
        total_cost = 0.0
        for cost_name in self:
            if ResourceCost.is_registered(cost_name):
                for cost_subtype in self[cost_name]:
                    if cost_subtype == Resource.TOKENS_IN:
                        if cost_name not in ResourceCost._custom_models:
                            costInfo = ModelCost(name=cost_name, input_tokens=int(self[cost_name][Resource.TOKENS_IN]), output_tokens=0)
                            total_cost += costInfo.input_cost
                        else: 
                            total_cost += self[cost_name][Resource.TOKENS_IN] * ResourceCost._custom_models[cost_name][Resource.TOKENS_IN]
                        #print(cost_name)
                        #print(costInfo)
                    elif cost_subtype == Resource.TOKENS_OUT:
                        if cost_name not in ResourceCost._custom_models:
                            costInfo = ModelCost(name=cost_name, input_tokens=0, output_tokens=int(self[cost_name][Resource.TOKENS_OUT]))
                            total_cost += costInfo.output_cost
                        else:
                            total_cost += self[cost_name][Resource.TOKENS_OUT] * ResourceCost._custom_models[cost_name][Resource.TOKENS_OUT]
                        #print(cost_name)
                        #print(costInfo)
                    else:
                        # Unknown expense, raise exception
                        if raise_on_uncalculable:
                            raise CannotEstimateCostError(f"Cannot calculate cost, cost subtype {cost_subtype} is unknown, please update ResourceCost.to_usd()")
                        return None  
            else:
                # Cannot compute if there is a key for something that isn't an LLM
                if raise_on_uncalculable:
                    raise CannotEstimateCostError(f"Cannot calculate cost, cost name {cost_name} is unknown, please update ResourceCost with ResourceCost.register_custom_model()")
                return None 

        # Do not round to avoid cumulative errors
        return total_cost

    def __getitem__(self, name: str) -> dict[Resource, float]:
        return self._resources[name]
    
    def __setitem__(self, key: str, item: dict[Resource, float]) -> None:
        self._resources[key] = item  

    def __contains__(self, item) -> bool:
        return item in self._resources

    def __iter__(self) -> Iterator[str]:
        return self._resources.__iter__()
    
    def __len__(self):
        return len(self._resources)

    def __add__(self, other: ResourceCost) -> ResourceCost:
        if not isinstance(other, ResourceCost):
            raise TypeError(f"Can only add ResourceCost instances, got {type(other).__name__}")
        
        self_copy = copy.deepcopy(self)
        for key in other._resources:
            if key not in self_copy._resources:
                self_copy._resources[key] = other[key]
            else:
                for subkey in other[key]:
                    if subkey in self_copy[key]:
                        self_copy[key][subkey] += other[key][subkey]
                    else:
                        self_copy[key][subkey] = other[key][subkey]
        return self_copy 

    @staticmethod
    def avg_and_dev(costs: list[ResourceCost]) -> dict[str, tuple[float, float]]:
        """Calculate average and standard deviation of costs across multiple ResourceCost instances.

        Aggregates costs by model and resource type, then computes mean and standard deviation
        for each combination. Useful for analyzing cost distributions across multiple runs or episodes.

        Args:
            costs: List of ResourceCost instances to aggregate.

        Returns:
            Dictionary mapping strings of the form '{model_name} {Resource}' to tuples of
            (mean, standard_deviation). For example: {'gpt-4o-mini Resource.TOKENS_IN': (1000.5, 50.2)}.
        """
        accumulator = defaultdict(lambda: list())

        for total_cost in costs:

            assert isinstance(total_cost, ResourceCost), total_cost

            for model in total_cost:
                for indiv_cost in total_cost[model]:
                    accumulator[f'{model} {indiv_cost}'].append(total_cost[model][indiv_cost])

        result = {}
        for key in accumulator:
            vals = np.array(accumulator[key])
            result[key] = (np.mean(vals), np.std(vals)) 

        return result
    
    def to_dict(self) -> dict[str, dict[str, float]]:
        """Convert the ResourceCost instance to a dictionary representation.

        Returns a nested dictionary where the outer keys are model names and the inner
        dictionaries map Resource enum string representations to their cost values.

        Returns:
            Dictionary of the form {model_name: {resource_str: cost_value}}.
            For example: {'gpt-4o-mini': {'Resource.TOKENS_IN': 1000.0, 'Resource.TOKENS_OUT': 500.0}}.
        """
        out = {}
        for key in self._resources:
            out[key] = {}
            for subkey in self._resources[key]:
                out[key][f'{subkey}'] = self._resources[key][subkey]
        return out 