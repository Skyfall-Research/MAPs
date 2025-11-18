import unittest
from unittest.mock import patch
from unittest import skip


def mocked_post_endpoint_create_ride(*args):
     print(args)
     if len(args) < 4:
          return {}
     if args[2] != "ride":
          return {}
     valid_args = ['x','y','ticketPrice','subtype', 'parkId', 'capacity', 'excitement','intensity']
     for arg in args[3]:
          if arg not in valid_args:
               return {}
     return {
          'message' : "Successfully created Park"
     }

def mocked_post_place_staff(*args):
     print(args)
     if len(args) < 4:
          return {}
     if args[2] != "staff":
          return {}
     valid_args = ['job','x','y', 'parkId']
     for arg in args[3]:
          if arg not in valid_args:
               return {}
     return {
          'message' : "Successfully Hired Staff"
     }


if __name__ == "__main__":
       unittest.main()




        

        




    