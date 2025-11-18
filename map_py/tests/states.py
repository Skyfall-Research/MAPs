import json 
from map_py.shared_constants import MAP_CONFIG

EMPTY_ENV4_STATE = {
  "difficulty": "medium",
  "layout": "undefined",
  "entrance": {
    "cleanliness": 0.9,
    "type": "entrance",
    "x": 0,
    "y": 0,
  },
  "exit": {
    "cleanliness": 0.9,
    "type": "exit",
    "x": 19,
    "y": 19,
  },
  "guestStats": {
    "avg_drink_shops_visited": 0,
    "avg_food_shops_visited": 0,
    "avg_happiness": 0,
    "avg_hunger": 0,
    "avg_money_spent": 0,
    "avg_rides_visited": 0,
    "avg_specialty_shops_visited": 0,
    "avg_steps_taken": 0,
    "avg_thirst": 0,
    "total_guests": 0
  },
  "guest_preferences": [
    "no preferences"
  ],
  "guest_survey_results": {
    "age_of_results": 0,
    "list_of_results": []
  },
  "rides": [],
  "shops": [],
  "staff": [],
  "state": {
    "available_entities": {
      "carousel": [
        "yellow"
      ],
      "drink": [
          "yellow"
      ],
      "ferris_wheel": [
        "yellow"
      ],
      "food": [
          "yellow"
      ],
      "janitor": [
        "yellow"
      ],
      "mechanic": [
          "yellow"
      ],
      "roller_coaster": [
        "yellow"
      ],
      "specialist": [
        "yellow"
      ],
      "specialty": [
          "yellow",
      ]
    },
    "expenses": 0,
    "fast_days_since_last_new_entity": 0,
    "horizon": 50,
    "medium_days_since_last_new_entity": 0,
    "money": 5000,
    "value": 5000,
    "sandbox_mode": False,
    "sandbox_steps": -1,
    "seed": None,
    "new_entity_available": False,
    "parkId": "14",
    "park_excitement": 0,
    "park_rating": 20,
    "prev_guest_happiness": 0.5,
    "research_speed": "none",
    "research_topic_index": -1,
    "research_operating_cost": 0,
    "research_topics": [
      "carousel",
      "drink",
      "ferris_wheel",
      "food",
      "janitor",
      "mechanic",
      "roller_coaster",
      "specialist",
      "specialty"
    ],
    "research_unresearched_entities": {
      "carousel": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "drink": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "ferris_wheel": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "food": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "janitor": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "mechanic": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "roller_coaster": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "specialist": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "specialty": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      }
    },
    "revenue": 0,
    "slow_days_since_last_new_entity": 0,
    "step": 7,
    "total_salary_paid": 0
  },
  "terrain": [
    {
      "cleanliness": 1,
      "type": "path",
      "x": 0,
      "y": 1
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 1,
      "y": 0
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 1,
      "y": 1
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 1
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 2
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 3
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 4
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 3,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 4,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 5,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 6,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 9
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 10
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 8,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 8,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 8,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 6
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 7
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 9
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 10
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 10,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 10,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 10,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 11,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 11,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 11,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 6
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 9
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 10
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 13,
      "y": 6
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 13,
      "y": 7
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 13,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 14,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 15,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 16,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 16,
      "y": 9
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 16,
      "y": 10
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 16,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 16,
      "y": 12
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 16,
      "y": 13
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 16,
      "y": 14
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 16,
      "y": 15
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 17,
      "y": 15
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 17,
      "y": 16
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 18,
      "y": 16
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 18,
      "y": 17
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 18,
      "y": 18
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 18,
      "y": 19
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 19,
      "y": 18
    }
  ]
}



COMPLEX_ENV4_STATE = {
  "difficulty": "medium",
  "layout": "undefined",
  "entrance": {
    "cleanliness": 0.9,
    "type": "entrance",
    "x": 0,
    "y": 0,
  },
  "exit": {
    "cleanliness": 0.9,
    "type": "exit",
    "x": 19,
    "y": 19,
  },
  "guestStats": {
    "avg_drink_shops_visited": 0,
    "avg_food_shops_visited": 0,
    "avg_happiness": 0.51,
    "avg_hunger": 1,
    "avg_money_spent": 15.03,
    "avg_rides_visited": 0,
    "avg_specialty_shops_visited": 0,
    "avg_steps_taken": 71.55,
    "avg_thirst": 1,
    "total_guests": 31
  },
  "guest_preferences": [
    "no preferences"
  ],
  "guest_survey_results": {
    "age_of_results": 7,
    "list_of_results": []
  },
  "rides": [
    {
      "avg_wait_time": 4,
      "breakdown_rate": 0.001,
      "avg_guests_per_operation": 0.83,
      "capacity": 6,
      "cleanliness": 0.96,
      "cost_per_operation": 1,
      "excitement": 1,
      "guests_entertained": 35,
      "intensity": 1,
      "out_of_service": False,
      "operating_cost": 193,
      "remaining_repair_time": 0,
      "revenue_generated": 700,
      "subclass": "yellow",
      "subtype": "carousel",
      "ticket_price": 2,
      "times_operated": 42,
      "total_wait_time": 100,
      "total_guests_queued": 25,
      "type": "ride",
      "uptime": 10,
      "unnorm_uptime": 5000,
      "x": 1,
      "y": 2
    }
  ],
  "shops": [
    {
      "cleanliness": 1,
      "guests_served": 3,
      "item_price": 15,
      "item_cost": MAP_CONFIG['shops']['specialty']['yellow']['item_cost'],
      "operating_cost": 40,
      "out_of_service": False,
      "revenue_generated": 735,
      "services_attempted": 500,
      "subclass": "yellow",
      "subtype": "specialty",
      "type": "shop",
      "x": 3,
      "y": 3,
      "uptime": 0.01,
      "inventory": 10,
      "order_quantity": 1000,
      "order_quantity": 1000,
    },
    {
      "cleanliness": 1,
      "guests_served": 21,
      "item_price": 6,
      "item_cost": MAP_CONFIG['shops']['food']['yellow']['item_cost'],
      "operating_cost": 20,
      "out_of_service": False,
      "revenue_generated": 1374,
      "services_attempted": 100,
      "subclass": "yellow",
      "subtype": "food",
      "type": "shop",
      "x": 3,
      "y": 4,
      "uptime": 0.21,
      "inventory": 32,
      "order_quantity": 33,
      "order_quantity": 33,
    }
  ],
  "staff": [
    {
      "id": "janitor-18",
      "salary": MAP_CONFIG['staff']['janitor']['yellow']['salary'],
      "subclass": "yellow",
      "success_metric": "amount_cleaned",
      "success_metric_value": 0,
      "operating_cost": 0,
      "tiles_traversed": 32,
      "type": "staff",
      "subtype": "janitor",
      "x": 1,
      "y": 2
    },
    {
      "id": "janitor-17",
      "salary": MAP_CONFIG['staff']['janitor']['blue']['salary'],
      "subclass": "blue",
      "success_metric": "amount_cleaned",
      "success_metric_value": 3,
      "operating_cost": 3,
      "tiles_traversed": 0,
      "type": "staff",
      "subtype": "janitor",
      "x": 2,
      "y": 2
    },
    {
      "id": "mechanic-10",
      "salary": MAP_CONFIG['staff']['mechanic']['green']['salary'],
      "subclass": "green",
      "success_metric": "repair_steps_performed",
      "success_metric_value": 0,
      "operating_cost": 0,
      "tiles_traversed": 0,
      "type": "staff",
      "subtype": "mechanic",
      "x": 10,
      "y": 11
    }
  ],
  "state": {
    "available_entities": {
      "carousel": [
        "yellow"
      ],
      "drink": [
          "yellow"
      ],
      "ferris_wheel": [
        "yellow"
      ],
      "food": [
          "yellow"
      ],
      "janitor": [
        "yellow"
      ],
      "mechanic": [
          "yellow"
      ],
      "roller_coaster": [
        "yellow"
      ],
      "specialist": [
        "yellow"
      ],
      "specialty": [
          "yellow",
      ]
    },
    "expenses": 161,
    "fast_days_since_last_new_entity": 0,
    "horizon": 50,
    "medium_days_since_last_new_entity": 0,
    "money": 2041,
    "value": 3000,  # TODO: Update
    "sandbox_mode": False,
    "sandbox_steps": -1,
    "seed": None,
    "new_entity_available": False,
    "parkId": "17",
    "park_excitement": 1,
    "park_rating": 57.25285284844752,
    "prev_guest_happiness": 0.8020912884890782,
    "research_speed": "none",
    "research_topic_index": -1,
    "research_operating_cost": 0,
    "research_topics": [
      "carousel",
      "drink",
      "ferris_wheel",
      "food",
      "janitor",
      "mechanic",
      "roller_coaster",
      "specialist",
      "specialty"
    ],
    "research_unresearched_entities": {
      "carousel": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "drink": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "ferris_wheel": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "food": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "janitor": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "mechanic": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "roller_coaster": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "specialist": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "specialty": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      }
    },
    "revenue": 466,
    "slow_days_since_last_new_entity": 0,
    "step": 17,
    "total_salary_paid": 80
  },
  "terrain": [
    {
      "cleanliness": 1,
      "type": "path",
      "x": 0,
      "y": 1
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 1,
      "y": 0
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 1,
      "y": 1
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 1
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 2
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 2,
      "y": 3
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 4
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 2,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 3,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 4,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 5,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 6,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 9
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 10
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 7,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 8,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 8,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 8,
      "y": 11
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 9,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 6
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 7
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 9
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 10
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 9,
      "y": 11
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 10,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 10,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 10,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 11,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 11,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 11,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 5
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 6
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 8
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 9
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 10
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 12,
      "y": 11
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 13,
      "y": 6
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 13,
      "y": 7
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 13,
      "y": 8
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 14,
      "y": 8
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 15,
      "y": 8
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 16,
      "y": 8
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 16,
      "y": 9
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 16,
      "y": 10
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 16,
      "y": 11
    },
    {
      "cleanliness": 0.98,
      "type": "path",
      "x": 16,
      "y": 12
    },
    {
      "cleanliness": 0.98,
      "type": "path",
      "x": 16,
      "y": 13
    },
    {
      "cleanliness": 0.99,
      "type": "path",
      "x": 16,
      "y": 14
    },
    {
      "cleanliness": 0.98,
      "type": "path",
      "x": 16,
      "y": 15
    },
    {
      "cleanliness": 0.98,
      "type": "path",
      "x": 17,
      "y": 15
    },
    {
      "cleanliness": 0.98,
      "type": "path",
      "x": 17,
      "y": 16
    },
    {
      "cleanliness": 0.98,
      "type": "path",
      "x": 18,
      "y": 16
    },
    {
      "cleanliness": 0.97,
      "type": "path",
      "x": 18,
      "y": 17
    },
    {
      "cleanliness": 0.98,
      "type": "path",
      "x": 18,
      "y": 18
    },
    {
      "cleanliness": 1,
      "type": "path",
      "x": 18,
      "y": 19
    },
    {
      "cleanliness": 0.97,
      "type": "path",
      "x": 19,
      "y": 18
    }
  ]
}


TEST_PROFIT_NO_RIDES = {"difficulty": "medium",
                        "layout": "undefined",
                        "entrance": {
    "cleanliness": 0.93,
    "type": "entrance",
    "x": 11,
    "y": 9,
  },
  "exit": {
    "cleanliness": 0.9,
    "type": "exit",
    "x": 3,
    "y": 15,
  },
                        "guestStats": {"avg_drink_shops_visited": 0, "avg_food_shops_visited": 0, "avg_happiness": 0, "avg_hunger": 0, "avg_money_spent": 0, "avg_rides_visited": 0, "avg_specialty_shops_visited": 0, "avg_steps_taken": 0, "avg_thirst": 0, "total_guests": 0}, 
                        "guest_preferences": [
                          "no preferences"
                        ],
                        "guest_survey_results": {
                          "age_of_results": 0,
                          "list_of_results": []
                        },
                        "terrain": [{"cleanliness": 1, "type": "path", "x": 0, "y": 0}, {"cleanliness": 1, "type": "path", "x": 1, "y": 0}, {"cleanliness": 1, "type": "path", "x": 2, "y": 0}, {"cleanliness": 1, "type": "path", "x": 2, "y": 15}, {"cleanliness": 1, "type": "path", "x": 2, "y": 16}, {"cleanliness": 1, "type": "path", "x": 2, "y": 17}, {"cleanliness": 1, "type": "path", "x": 3, "y": 0}, {"cleanliness": 1, "type": "path", "x": 3, "y": 1}, {"cleanliness": 1, "type": "path", "x": 3, "y": 2}, {"cleanliness": 1, "type": "path", "x": 3, "y": 3}, {"cleanliness": 1, "type": "path", "x": 3, "y": 4}, {"cleanliness": 1, "type": "path", "x": 3, "y": 5}, {"cleanliness": 1, "type": "path", "x": 3, "y": 6}, {"cleanliness": 1, "type": "path", "x": 3, "y": 7}, {"cleanliness": 1, "type": "path", "x": 3, "y": 8}, {"cleanliness": 1, "type": "path", "x": 3, "y": 9}, {"cleanliness": 1, "type": "path", "x": 3, "y": 10}, {"cleanliness": 1, "type": "path", "x": 3, "y": 11}, {"cleanliness": 1, "type": "path", "x": 3, "y": 12}, {"cleanliness": 1, "type": "path", "x": 3, "y": 13}, {"cleanliness": 1, "type": "path", "x": 3, "y": 14}, {"cleanliness": 1, "type": "path", "x": 4, "y": 0}, {"cleanliness": 1, "type": "path", "x": 4, "y": 11}, {"cleanliness": 1, "type": "path", "x": 5, "y": 0}, {"cleanliness": 1, "type": "path", "x": 5, "y": 11}, {"cleanliness": 1, "type": "path", "x": 6, "y": 0}, {"cleanliness": 1, "type": "path", "x": 6, "y": 1}, {"cleanliness": 1, "type": "path", "x": 6, "y": 11}, {"cleanliness": 1, "type": "path", "x": 7, "y": 1}, {"cleanliness": 1, "type": "path", "x": 7, "y": 2}, {"cleanliness": 1, "type": "path", "x": 7, "y": 11}, {"cleanliness": 1, "type": "path", "x": 8, "y": 2}, {"cleanliness": 1, "type": "path", "x": 8, "y": 11}, {"cleanliness": 1, "type": "path", "x": 9, "y": 2}, {"cleanliness": 1, "type": "path", "x": 9, "y": 11}, {"cleanliness": 1, "type": "path", "x": 10, "y": 0}, {"cleanliness": 1, "type": "path", "x": 10, "y": 1}, {"cleanliness": 1, "type": "path", "x": 10, "y": 2}, {"cleanliness": 1, "type": "path", "x": 10, "y": 3}, {"cleanliness": 1, "type": "path", "x": 10, "y": 4}, {"cleanliness": 1, "type": "path", "x": 10, "y": 5}, {"cleanliness": 1, "type": "path", "x": 10, "y": 6}, {"cleanliness": 1, "type": "path", "x": 10, "y": 7}, {"cleanliness": 1, "type": "path", "x": 10, "y": 8}, {"cleanliness": 1, "type": "path", "x": 10, "y": 9}, {"cleanliness": 1, "type": "path", "x": 10, "y": 10}, {"cleanliness": 1, "type": "path", "x": 10, "y": 11}, {"cleanliness": 1, "type": "path", "x": 11, "y": 2}, {"cleanliness": 1, "type": "path", "x": 12, "y": 2}, {"cleanliness": 1, "type": "path", "x": 12, "y": 9}, {"cleanliness": 1, "type": "path", "x": 13, "y": 2}, {"cleanliness": 1, "type": "path", "x": 13, "y": 9}, {"cleanliness": 1, "type": "path", "x": 14, "y": 2}, {"cleanliness": 1, "type": "path", "x": 14, "y": 9}, {"cleanliness": 1, "type": "path", "x": 15, "y": 2}, {"cleanliness": 1, "type": "path", "x": 15, "y": 7}, {"cleanliness": 1, "type": "path", "x": 15, "y": 8}, {"cleanliness": 1, "type": "path", "x": 15, "y": 9}, {"cleanliness": 1, "type": "path", "x": 16, "y": 2}, {"cleanliness": 1, "type": "path", "x": 16, "y": 7}, {"cleanliness": 1, "type": "path", "x": 16, "y": 9}, {"cleanliness": 1, "type": "path", "x": 17, "y": 2}, {"cleanliness": 1, "type": "path", "x": 17, "y": 3}, {"cleanliness": 1, "type": "path", "x": 17, "y": 4}, {"cleanliness": 1, "type": "path", "x": 17, "y": 5}, {"cleanliness": 1, "type": "path", "x": 17, "y": 6}, {"cleanliness": 1, "type": "path", "x": 17, "y": 7}, {"cleanliness": 1, "type": "path", "x": 17, "y": 9}, {"cleanliness": 1, "type": "path", "x": 18, "y": 2}, {"cleanliness": 1, "type": "path", "x": 18, "y": 9}, {"cleanliness": 1, "type": "path", "x": 19, "y": 2}, {"cleanliness": 1, "type": "path", "x": 19, "y": 3}, {"cleanliness": 1, "type": "path", "x": 19, "y": 4}, {"cleanliness": 1, "type": "path", "x": 19, "y": 5}, {"cleanliness": 1, "type": "path", "x": 19, "y": 6}, {"cleanliness": 1, "type": "path", "x": 19, "y": 7}, {"cleanliness": 1, "type": "path", "x": 19, "y": 8}, {"cleanliness": 1, "type": "path", "x": 19, "y": 9}], 
                        "rides": [], 
                        "shops": [],
                        "staff": [], 
                        "state": {"available_entities": {      "carousel": [
        "yellow"
      ],
      "drink": [
          "yellow"
      ],
      "ferris_wheel": [
        "yellow"
      ],
      "food": [
          "yellow"
      ],
      "janitor": [
        "yellow"
      ],
      "mechanic": [
          "yellow"
      ],
      "roller_coaster": [
        "yellow"
      ],
      "specialist": [
        "yellow"
      ],
      "specialty": [
          "yellow",
      ]}, 

    "expenses": 0, "fast_days_since_last_new_entity": 0, 
    "horizon": 50,
    "medium_days_since_last_new_entity": 0, "money": 500, "value": 500, "sandbox_mode": False,
    "sandbox_steps": -1,
    "seed": None,"new_entity_available": False, "parkId": "0", 
    "park_excitement": 0, "park_rating": 10, "prev_guest_happiness": 0.5, 
    "research_speed": "none",
    "research_topic_index": -1,
    "research_operating_cost": 0,
    "research_topics": [
      "carousel",
      "drink",
      "ferris_wheel",
      "food",
      "janitor",
      "mechanic",
      "roller_coaster",
      "specialist",
      "specialty"
    ],
    "research_unresearched_entities": {
      "carousel": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "drink": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "ferris_wheel": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "food": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "janitor": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "mechanic": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "roller_coaster": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "specialist": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      },
      "specialty": {
        "order": [
          "blue",
          "green",
          "red"
        ],
        "progress": {
          "blue": 100,
          "green": 200,
          "red": 400
        }
      }
    },
    "revenue": 0, "slow_days_since_last_new_entity": 0, "step": 0, "total_salary_paid": 0}}

