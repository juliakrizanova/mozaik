# coding: utf-8
"""
Definition of the component interfaces. These interfaces are not currently
checked or enforced.
"""

from NeuroTools.parameters import ParameterSet
from NeuroTools.signals.spikes import SpikeList
from space import VisualObject, TRANSPARENT
from MozaikLite import __version__
import logging
import os
from string import Template
import numpy

logger = logging.getLogger("MozaikLite")

class VisualStimulus(VisualObject):
    """Abstract base class for visual stimuli."""
    
    version = __version__ # for simplicity, we take the global version, but it
                          # would be more efficient to take the revision for the
                          # last time this particular file was changed.
    
    def __init__(self, frame_duration, size_in_degrees, location, max_luminance):
        VisualObject.__init__(self, location, size_in_degrees) # for now, we always put the stimulus in the centre of the visual field
        self.frame_duration = frame_duration
        self.max_luminance = max_luminance
        self.parameters = ParameterSet({
                            'frame_duration': frame_duration,
                            'size_in_degrees': size_in_degrees,
                            'max_luminance': max_luminance,
                            'location': location
                          })
        self.input = None
        self._frames = self.frames()
        self.update()
    
    def frames(self):
        """
        Return a generator which yields the frames of the stimulus in sequence.
        Each frame is returned as a tuple `(img, variables)` where
        `img` is a numpy array containing the image and `variables` is a list of
        variable values (e.g., orientation) associated with that frame.
        """
        raise NotImplementedError("Must be implemented by child class.")

    def update(self):
        """
        Sets the current frame to the next frame in the sequence.
        """
        try:
            self.img, self.variables = self._frames.next()
        except StopIteration:
            self.visible = False
        else:
            assert self.img.min() >= 0 or self.img.min() == TRANSPARENT, "frame minimum is less than zero: %g" % self.img.min()
            assert self.img.max() <= self.max_luminance, "frame maximum (%g) is greater than the maximum luminance (%g)" % (self.img.max(), self.max_luminance)
        self._zoom_cache = {}
    
    def reset(self):
        """
        Reset to the first frame in the sequence.
        """
        self.visible = True
        self._frames = self.frames()
        self.update()

    def export(self, path=None):
        """
        Save the frames to disk. Returns a list of paths to the individual
        frames.
        
        path - the directory in which the individual frames will be saved. If
               path is None, then a temporary directory is created.
        """
        raise NotImplementedError
    
    def next_frame(self):
        """For creating movies with NeuroTools.visualization."""
        self.update()
        return [self.img]
  

class MozaikLiteParametrizeObject(object):
    """Base class for for all MozailLite objects using the dynamic parametrization framwork."""
    
    required_parameters = ParameterSet({})
    version = __version__

    def check_parameters(self, parameters):
            def walk(tP, P, section=None):
                if set(tP.keys()) != set(P.keys()):
                    raise KeyError("Invalid parameters for %s.%s Required: %s. Supplied: %s" % (self.__class__.__name__, section or '', tP.keys(), P.keys()))
                for k,v in tP.items():
                    if isinstance(v, ParameterSet):
                        assert isinstance(P[k], ParameterSet), "Type mismatch: %s !=  ParameterSet, for %s " % (type(P[k]),P[k]) 
                        walk(v, P[k],section=k)
                    else:
                        assert isinstance(P[k], v), "Type mismatch: %s !=  %s, for %s" % (v,type(P[k]),P[k])
            try:
                # we first need to collect the required parameters from all the classes along the parent path
                new_param_dict={}
                for cls in self.__class__.__mro__:
                # some parents might not define required_parameters 
                # if they do not require one or they are the object class
                    if hasattr(cls, 'required_parameters'):
                        new_param_dict.update(cls.required_parameters.as_dict())
                walk(ParameterSet(new_param_dict), parameters)
            except AssertionError as err:
                raise Exception("%s\nInvalid parameters.\nNeed %s\nSupplied %s" % (err,ParameterSet(new_param_dict),
                                                                               parameters))  
                                                                               
                                                                               
    def __init__(self, parameters):
            """
            """
            self.check_parameters(parameters)
            self.parameters = parameters
                                                                                   
class MozaikComponent(MozaikLiteParametrizeObject):
    """Base class for visual system components and connectors."""
    
    def __init__(self, network, parameters):
        """
        """
        MozaikLiteParametrizeObject.__init__(self, parameters)
        self.network = network
    

class VisualSystemConnector(MozaikComponent):
    """Base class for objects that connect visual system components."""
    version = __version__
    
    def __init__(self, network, source, target, parameters):
        logger.info("Creating %s between %s and %s" % (self.__class__.__name__,
                                                       source.__class__.__name__,
                                                       target.__class__.__name__))
        MozaikComponent.__init__(self, network, parameters)
        self.network.register_connector(self)
        self.sim = self.network.sim
        self.source = source
        self.target = target
        self.input = source
        self.target.input = self
        
    def describe(self, template='default', render=lambda t,c: Template(t).safe_substitute(c)):
        context = {
            'name': self.__class__.__name__,
            'source': {
                'name': self.source.__class__.__name__,
            },
            'target': {
                'name': self.target.__class__.__name__,
            },
            'projections': [prj.describe(template=None) for prj in self.projections]
        }
        if template:
            render(template, context)
        else:
            return context
        
  
