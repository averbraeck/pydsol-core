"""
This module contains the exceptions that are used in the pydsol code. 
"""

class DSOLError(Exception):
    """General Exception class for pydsol."""
    pass

class EventError(Exception):
    """General Exception for working with Events and publish/subscribe"""
    pass
