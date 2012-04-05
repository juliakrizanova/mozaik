"""
This module contains the definition of the AnalysisDataStructure API and implementation of 
some basic analysis data structures.
"""
import numpy
from mozaik.stimuli.stimulus_generator import parse_stimuls_id
import param
from param.parameterized import Parameterized

class AnalysisDataStructure(Parameterized):
      """
      AnalysisDataStructure encupsulates data that a certain Analysis class generates.
      An analysis class can generate several AnalysisDataStructure's (ADSs) and one ADS
      can be generated by several Analysis classes
      the goal is to offer a common interface of such data for plotting 
      i.e. many analysis can generate 2D tuning curves of several kinds but they all
      share common data structure and can be plotted in a common way
      
      One important aspect of the ADS design is the notion of parameters as oposed to 
      inputs. Each ADS should define number of Parameters (see the documentation on Parameters).
      The importance of parameters is that they will offer a way to identify the ADS in data 
      store (see analysis_data_structure_parameter_filter_query in queries). Furthermore the
      constructor of the AnalysisDataStructure can accept inputs, which are standard variables 
      that should correspond to the data that is actually stored in the ADS.
      
      The three parameters that each ADS has are:
      
      identifier - 
          An important parameter of each AnalysisDataStructure is identifier which is used to 
          identify data structures of common type in storage facilities.
          Currently different datastructures with common interface should share the identifiers
          but it is not clear this is needed. If it turns out such sharing is not neccessary it 
          might be abolished and there will be one-to-one mapping between AnalysisDataStructure classes
          and identifiers.
      
      analysis_algorithm - 
          The identity (name) of the analysis class that produced this analysis data structure
      
      tags - 
          In complicated workflows it might become difficult to design a filter to extract the right 
          set of recordings or analysis data structures for a given analysis or visualization. 
          We do not want users to define multiple AnalysisDataStructures that hold the same 
          kind of data only to be able to tell them appart.
                  
          Therefore, we also allow all analysis data structures to contain a list of tags
          (which are strings) that one can add during their creation (or later) and use 
          them to later for their identification in DataStore. Queries are written that 
          support filtering of ADSs based on tags.
          
          However, in general, we encourage users to use filter methods rather that tags to perform their
          plotting/analysis whenever possible!
      """
      
      identifier = param.String(instantiate=True,doc=""" The identifier of the analysis data structure""")
      analysis_algorithm = param.String(instantiate=True,doc=""" The identifier of the analysis data structure""")
      tags = param.List(default=[],instantiate=True,doc="""The list of tags to attach""")
      
      def __init__(self,**params):
          Parameterized.__init__(self,**params)

          
class TuningCurve(AnalysisDataStructure):
        """
             Tuning curve holds data of a tuning curves with respect to a certain paramter of a stimulus.
             
             It is assumed that all other paramters are either: 
              * collpased (i.e. they have been averaged out such as phase or trials in case of orientation tuning)
              * those that are unclopased should be tread as the paramters of 
                the tuning curve (i.e. orientation tuning curves taken at different contrasts)
            
             sheet_name 
                    - in which sheet the data were recorded
             values     
                    - is a list of lists, members of the outer list correspond 
                      to the value of the tuning curve for a stimulus at the same position in the stimuli_ids
                      the inner lists contain the actual values for the measured neurons
             
             stimuli_ids 
                    - see values description
             
             parameter_index 
                    - the parameter position in the stimulus id against which the tuning curve was computed
             
             y_axis_name
                    - name of the tuning curve y axis
             
             y_axis_units
                    - quantities units of the y axis
        """
        
        sheet_name = param.String(instantiate=True,doc=""" The identifier of the analysis data structure""")
        
        def __init__(self,values,stimuli_ids,parameter_index,y_axis_name,y_axis_units,**params):
            AnalysisDataStructure.__init__(self,identifier = 'TuningCurve',**params)
            self.values = values
            self.stimuli_ids = stimuli_ids
            self.parameter_index = parameter_index
            self.y_axis_name = y_axis_name
            self.y_axis_units = y_axis_units

        def to_dictonary_of_tc_parametrization(self):
            """
            Returns dictionary where keys correspond to stimuli ids (essentially parametrizations of the Tuninc Curve)
            with the dimension through which tuning curve runs replaced with x.
            The values are tuple of lists (levels,xaxis), where levels is the value of the tuning curve on the 'yaxis' and the 'xaxis' corresponds
            to the value of the stimulus in the dimension through which the tuning curve runs, at which the level is achieved.
            Essentially to plot the given parametrization of tuning curve one does plot(xaxis,levels).
            
            Finally note each member of levels field is a array containing levels for different neurons.
            """
            
            self.d = {}
            for (v,s) in zip(self.values,self.stimuli_ids):
                s = parse_stimuls_id(s)
                val = float(s.parameters[self.parameter_index])
                s.parameters[self.parameter_index]='x'
                
                if self.d.has_key(str(s)):
                   (a,b) = self.d[str(s)] 
                   a.append(v)
                   b.append(val)
                else:
                   self.d[str(s)]  = ([v],[val]) 
            
            for k in self.d:
                (a,b) = self.d[k]
                self.d[k] = (numpy.array(a),b)
            
            return self.d

class CyclicTuningCurve(TuningCurve):
        """
        TuningCurve with over periodic quantity
        
        perdiod - the period of the parameter over which the tuning curve is measured, i.e. pi for orientation
                  all the values have to be in the range <0,period)
        """
        def __init__(self,period,*args,**params):
            TuningCurve.__init__(self,*args,**params)
            self.identifier = 'CyclicTuningCurve'
            self.period = period    
            # just double check that none of the stimuly has the corresponding parameter larger than period 
            for s in self.stimuli_ids:
                s = parse_stimuls_id(s)
                v = float(s.parameters[self.parameter_index])
                if v < 0 or v >= self.period:
                   raise ValueError("CyclicTuningCurve with period " + str(self.period) + ": "  + str(v) + " does not belong to <0," + str(self.period) + ") range!") 


class PerNeuronValue(AnalysisDataStructure):
      """
      Data structure holding single value per neuron.
      
      values
            - the vector of values one per neuron
      
      value_name
            - The name of the value.
      
      value_units
            - quantities unit describing the units of the value
      
      sheet_name
            - The name of the sheet to which the data correspond
      
      period
            - The period of the value. If value is not periodic period=None
      """
      
      value_name = param.String(instantiate=True,doc="""The name of the value.""")
      sheet_name = param.String(instantiate=True,doc="""The name of the sheet to which the data correspond.""")
      
      def __init__(self,values,value_units,tags,period=None,**params):
           AnalysisDataStructure.__init__(self,identifier = 'PerNeuronValue',**params)
           self.value_units = value_units
           self.period = period
           self.values = values

class AnalysisDataStructure1D(AnalysisDataStructure): 
      """
      Data structure representing 1D data.
      All data corresponds to the same axis name and units.
      Explicitly specifies the axis - their name and units.
      Note that at this stage we do not assume the structure in
      which the data is stored.
      Also the class can hold multiple instances of 1D data.
      
      It uses the quantities package to specify units.
      If at all possible all data stored in numoy arrays shoukd
      be quantities arrays with matching units!
      
      x_axis_name -
            the name of the x axis
      y_axis_name -
            the name of the y axis
      x_axis_untis -
            the quantities units of x axis
      y_axis_units -
            the quantities units of y axis
      """
      
      x_axis_name = param.String(instantiate=True,doc="""the name of the x axis.""")
      y_axis_name = param.String(instantiate=True,doc="""the name of the y axis.""")
        
      
      def __init__(self,x_axis_units,y_axis_units,**params):
           AnalysisDataStructure.__init__(self,**params)
           self.x_axis_units = x_axis_units
           self.y_axis_units = y_axis_units
        
class AnalogSignalList(AnalysisDataStructure1D):
       """
         This is a simple list of Neo AnalogSignal objects.

         asl - 
                the variable containing the list of AnalogSignal objects, in the order corresponding to the 
                order of neurons indexes in the indexes parameter
         indexes - 
                list of indexes of neurons in the original Mozaik sheet to which the AnalogSignals correspond
                
         sheet_name -
                The sheet from which the data were collected
       """
       
       sheet_name = param.String(instantiate=True,doc="""The sheet from which the data were collected.""")
       
       def __init__(self,asl,indexes,x_axis_units,y_axis_units,**params):
           AnalysisDataStructure1D.__init__(self,x_axis_units,y_axis_units,identifier = 'AnalogSignalList',**params)
           self.asl = asl
           self.indexes = indexes

class ConductanceSignalList(AnalysisDataStructure1D):
       """
         This is a simple list of Neurotools AnalogSignal objects representing the conductances
         The object holds two lists, one for excitatory and one for inhibitory conductances

         e_asl - 
            the variable containing the list of AnalogSignal objects corresponding to excitatory conductances,
            in the order corresponding to the order of neurons indexes in the indexes parameter
         i_asl - 
            the variable containing the list of AnalogSignal objects corresponding to inhibitory conductances,
            in the order corresponding to the order of neurons indexes in the indexes parameter
         indexes - 
            list of indexes of neurons in the original Mozaik sheet to which the AnalogSignals correspond
         sheet_name -
                The sheet from which the data were collected
       """
       
       sheet_name = param.String(instantiate=True,doc="""The sheet from which the data were collected.""")
        
       def __init__(self,e_con,i_con,indexes,**params):
           assert e_con[0].units == i_con[0].units
           AnalysisDataStructure1D.__init__(self,e_con[0].sampling_rate.units,e_con[0].units,x_axis_name='time',y_axis_name='conductance',identifier = 'ConductanceSignalList',**params)
           self.e_con = e_con
           self.i_con = i_con
           self.indexes = indexes
