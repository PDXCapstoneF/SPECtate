"""
This module defines ways to validate that a run is compliant
or not according to https://www.spec.org/jbb2015/docs/runrules.pdf.
"""
from schema import Schema, And, Or, Optional
from src.validate import is_stringy

def compliant(props=None):
    """
    Returns a boolean representing whether or not a run is compliant.
    Props is a dictionary of key => value pairs representing SPECjbb properties.
    """
    if props is None:
        return True

    try:
        return CompliantRunSchema.validate(props) is not None
    except Exception:
        return False

CompliantRunSchema = Schema({
    "specjbb.group.count": And(int, lambda group_count: group_count >= 1),
    "specjbb.txi.pergroup.count": And(int, lambda injector_count: injector_count >= 1),
    "specjbb.mapreducer.pool.size": And(int, lambda pool_size: pool_size >= 2),
    is_stringy: object,
    })
