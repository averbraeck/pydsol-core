"""
This module contains generic utilities for the pydsol code. 
"""
import logging
from typing import Any
import sys


class DSOLError(Exception):
    """General Exception class for pydsol."""
    pass

logging.basicConfig(level=logging.DEBUG,
        format='%(levelname)s: %(module)s.%(funcName)s: %(message)s')

def get_module_logger(mod_name: str, level=logging.CRITICAL):
    logger = logging.getLogger(mod_name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler(stream=sys.stdout)
        logger.addHandler(handler)
    msg_format = '%(levelname)s: %(module)s.%(funcName)s: %(message)s'
    formatter = logging.Formatter(fmt=msg_format)
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    logger.setLevel(level)
    return logger

logger = get_module_logger('utils')


class Assert():
    """
    The Assert class contains a number of utilities that are easy to use 
    to test preconditions (or postconditions) in a method.
    
    Methods
    -------
    istype
        Assert that a variable is an exact instance of a certain type
    subtype
        Assert that a variable is an instance of a type (or subtype)
    subtypes
        Assert that a variable is an instance of any of a list of typrs
    that
        Assert that a certain condition is met
    """
    
    @staticmethod
    def istype(var: Any, varname: str, type_: type, 
               error_class: Exception=DSOLError):
        """
        Assert that the variable 'var' is of type 'type_' (and not a subtype).
        
        Parameters
        ----------
        var: Any
            the variable to check
        varname: str
            the name of the variable to use in the message
        type_: type
            the type to check for. The type of var should be exactly the same
        error_class: Exception, optional
            the exception to throw; defaults to DSOLError
        """
        if type(var) == type_:
            return
        raise error_class(\
            f"parameter {varname} is not of type {type_.__name__}")
            
    
    @staticmethod
    def subtype(var: Any, varname: str, type_: type, 
               error_class: Exception=DSOLError):
        """
        Assert that the variable 'var' is an instance of type_ or an instance
        of a subtype of type_.
        
        Parameters
        ----------
        var: Any
            the variable to check
        varname: str
            the name of the variable to use in the message
        type_: type
            the type to check for
        error_class: Exception, optional
            the exception to throw; defaults to DSOLError
        """
        if isinstance(var, type_):
            return
        raise error_class(\
            f"parameter {varname} is not an instance of {type_.__name__}")
    
    @staticmethod
    def anytype(var: Any, varname: str, types: list[type], 
               error_class: Exception=DSOLError):
        """
        Assert that the variable 'var' is an instance of any of the given
        types in the type list.
        
        Parameters
        ----------
        var: Any
            the variable to check
        varname: str
            the name of the variable to use in the message
        types: list[type]
            the types to check for; ok if var is a subtype of any of the types
        error_class: Exception, optional
            the exception to throw; defaults to DSOLError
        """
        for type_ in types:
            if isinstance(var, type_):
                return
        s = [type_.__name__ for type_ in types]
        raise error_class(\
            f"parameter {varname} is not an instance of {s}")

    @staticmethod
    def that(condition: bool, error_class: Exception, 
             message: str, *args, **kwargs):
        """
        Assert that a certain condition is met, otherwise raise an error.
        
        Parameters
        ----------
        condition: bool
            the condition as an outcome of a check
        error_class: Exception
            the exception to throw
        message: str
            the message to print in the error in case of failure
        *args
            arguments to use in the formatting of the error string
        **kwargs
            arguments to use in the formatting of the error string
        """
        if not condition:
            raise error_class(message.format(*args, **kwargs))
