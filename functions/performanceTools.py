__doc__ = "Tools for egammaMVACalibUtils"

import numpy as np
import re
from itertools import chain, combinations, izip, product

# from http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned 
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
        try:
            self.__name__ = func.__name__
        except AttributeError:
            pass
    
    def __call__(self, *args):
        key = self.doCache(args)
        try:
            return self.cache[key]
        except KeyError:
            value = self.func(*args)
            self.cache[key] = value
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            print "Function (%s) and/or args (%s) are uncachable:" % (self.func.__name__, args)
            return self.func(*args)
      
    def doCache(self, args):
         return args
      
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)
    

class memoizedHashlib(memoized):
    "Use hashlib to memoize numpy ndarray"
    def doCache(self, args):
        import hashlib
        return tuple(hashlib.sha1(i).hexdigest() for i in args)



def subtract(*lists):
  "Return the subtraction of the given iterables"
  return reduce(set.__sub__, map(set,lists[1:]), set(lists[0]))


def binData(data, binning, indices=None):
    """binData(data, binning, indices=None)
       
       returns an array of numpy arrays containing the data split according to the given
       binning in  N-dimensions, including underflows and overflows. 
       Defines the indices using np.digitize if not given (only works for 1-D binning)

       data: a 1D array, the data to be binned
       binning: an array or list of arrays containing the bin edges for all axes
               (requires multi-dimensional indices if Ndim > 1)
       indices: an array or list of arrays containing the result of np.digitize in
                each dimension
       """
    if any( hasattr(i, '__iter__') for i in binning ): # binning is nested, i.e. N-dim
        shape = [len(i)+1 for i in binning]
    else:
        shape = (len(binning)+1, )
    binnedData = np.empty(shape, dtype=object)
    if indices is None:
        indices = np.digitize(data, binning)
    elif len(np.asarray(indices).shape) > 1:
        # Convert N-dim indices into 1-D. Slow...
        indices = [np.ravel_multi_index(i, shape) for i in np.asarray(indices).T]
    for i, _ in np.ndenumerate(binnedData):
      ind = np.ravel_multi_index( i, shape )
      binnedData[i] = data[ind == indices]
    return binnedData


def getIndicesForBinning(values, binning):
    """getIndicesForBinning(values, binning) -> 
    Return a list with the indices that would bin the data according to the binning,
    i.e. one can call later data[bin1], data[bin2], ..."""
    indices = [ [] for i in binning ] 
    indices.append( [] ) # add overflow bin
    for index,bin in enumerate(np.digitize(values, binning)):
        indices[bin].append(index)
    return indices


def binDataFromIndices(data, indices):
    """binDataFromIndices(data, *indices)
    Return a ndarray
    """
    return np.array([data[i] for i in indices], dtype=object)

def binData1(data, binning, bins = None, weights = None):
    """
    bin data according to bin:
    data -- the data to be binned
    binnings -- the edges for the binning, for all axis: [[0, 0.6, 2.5], [0, 10, 200]]
    bin -- the index for the binning: [[1,2,1, ...], [...]]; len(bin[i]) == len(data)
    """
    shape = [len(i) + 1 for i in binning]
    binnedData = np.zeros(np.product(shape), dtype=object )
    binnedData[:] = [[] for i in xrange(np.product(shape))]
    binnedData = binnedData.reshape(shape)
    for bin, value in izip(izip(*bins), data):
        binnedData[bin].append(value)
    return binnedData

def binData2(data, binning, bins = None, weights = None): # fastest
    "binData2(data, binning, bins = None, weights = None)"
    shape = [len(i) + 1 for i in binning]
    binnedData = {}
    for bin, value in izip(izip(*bins), data):
        try:
            binnedData[bin].append(value)
        except KeyError:
            binnedData[bin] = [value]
    # convert to numpy.ndarray
    bd = np.empty(shape, dtype=object)
    for i,j in np.ndenumerate(bd):
        bd[i] = np.array(binnedData.get(i, []) )
  
#   if len(shape) == 1:
#     bd[np.transpose(binnedData.keys())] = map(np.array, binnedData.values())
#   else:
# #     bd[np.transpose(binnedData.keys())] = map(np.array, binnedData.values())
#     bd[zip(*binnedData.keys())] = map(np.array, binnedData.values())
    return bd

def binDataAndWeights(data, binning, bins = None, weights = None):
    if weights is None:
        return binData2(data, binning, bins), None
    shape = [len(i) + 1 for i in binning]
    binnedData = {}
    binnedWeights = {}
    for bin, value, w in izip(izip(*bins), data, weights):
        try:
            binnedData[bin].append(value)
            binnedWeights[bin].append(w)
        except KeyError:
            binnedData[bin] = [value]
            binnedWeights[bin] = [w]
    # convert to numpy.ndarray
    bd = np.empty(shape, dtype=object)
    bw = np.empty(shape, dtype=object)
    for i,j in np.ndenumerate(bd):
        bd[i] = np.array(binnedData.get(i, []) )
        bw[i] = np.array(binnedWeights.get(i, []) )
    return bd, bw
  


def binData3(data, binning, bins = None):
  shape = [len(i) + 1 for i in binning]
  Ndim = len(shape)
  bins = np.transpose(bins)
  binnedData = np.zeros(shape, dtype=object )
  for i in product(*map(range, shape)): 
    binnedData[i] = data[np.all( bins == i, axis=1 )]
  return binnedData

def sliceUnderOverflows(x):
  "Return a slice of the ndarray without the first and last element of each dimension"
  Ndim = len(x.shape)
  return x[ [slice(1,-1)]*Ndim ]

def getFcnName(f):
  "Return the function name, also if it is decorated with errorize / vectorize"
  if isinstance(f, np.lib.function_base.vectorize):
    try:
      return getFcnName(f.pyfunc)
    except AttributeError:
      print "Catched AttributeError: no attribute 'pyfunc' "

  try:
    return f.__name__
  except AttributeError:
    if hasattr(f, 'thefunc'):
      return getFcnName(f.thefunc)
    elif hasattr(f, 'f'):
      return getFcnName(f.f)
    raise
      
def getMidPoint(x):
    "Given a ndarray, return the midpoint between adjacent elements"
    return (x[1:] + x[:-1])/2


class BinningDescription(object):
    __slots__ = ("axis_names", "axis_titles", "binnings", "selection")
    def __init__(self, binnings, axis_names, axis_titles=None, selection=None, use_extraflows=True):
        """
        example: binnings = ((0, 0.6, 1.425), (10, 25, 50))
        axis_names = ('ph_cl_eta', 'ph_cl_E')
        axis_title = ('|#eta|', 'E_{cl}')
        selection = {'ph_cl_phi": (0., 3.14/2.)}

        if use_extraflows is True (default) bin index counts from 1: bin 0 is the underflow,
        bin n+1 is the overflow bin
        """
        import RootTools
        self.axis_names = tuple(axis_names)
        self.axis_titles = tuple(axis_titles) if axis_titles is not None else tuple(axis_names)
        if any(len(x)!=len(binnings) for x in (self.axis_names, self.axis_titles)):
            raise ValueError("inputs don't have the same length")
        self.binnings = [RootTools.binning2array(b) for b in binnings]
        self.selection = selection if selection else dict()
        
    def __iter__(self):        
        iter = izip(self.binnings, self.axis_names, self.axis_titles)    
        for i in iter:
            yield dict(zip(("binning", "name", "title"), i))
    
    def subBinningDescriptionFromAxis(self, list_axis):
        """
        return a BinningDescription slice, using only axis in list_axis, for example:
        * list_axis = (1,2) return a BinnedDescription using only the second and third axis
        * list_axis = (2, "ph_cl_eta") return a BinnedDescription using only the third and
                      ph_cl_eta axis
        """
        axis_to_use = [axis if type(axis) is int else self.axis_index(axis) for axis in list_axis]
        return BinningDescription([self.binnings[i] for i in axis_to_use],
                                  [self.axis_names[i] for i in axis_to_use],
                                  [self.axis_titles[i] for i in axis_to_use])

    def subBinningDescriptionFromSelection(self, list_axis):
        """
        return a BinningDescription slice, for example:
        * list_axis = {2: None} return a BinningDescription without the third axis
                      (None means inclusive)
        * list_axis = {1: 3} return a BinningDescripion without the second axis, in
                      this case because we're selecting only the third bin of the first axis
        * list_axis = {2:None, 1:3} combine the first two
        * list_axis = {1: slice(1,3)} return a BinningDescription withot the first axis, in
                      this case because we're selecting only the bins from 1 to 2 of the second axis
        you can also use names instead of number for the key
        """
        keys = [k if type(k) == int else self.axis_index(k) for k in list_axis]
        axis_to_use = [k for k in range(self.dim()) if k not in keys]
        other_axis = dict([(self.axis_names[k], self.get_range(k,v))
                           for k, v in zip(keys, list_axis.itervalues()) if v is not None])
        return BinningDescription([self.binnings[i] for i in axis_to_use],
                                  [self.axis_names[i] for i in axis_to_use],
                                  [self.axis_titles[i] for i in axis_to_use],
                                  selection = other_axis)
    
    def get_range(self, axis, index, inclusive_range=False):
        """
        return a tuple of left, right edge. Remember the index count from 1.
        """
        if type(axis) is str:
            axis = self.axis_index(axis)
        axis_binning = self.binnings[axis]
        if type(index) is int:
            low_edge = axis_binning[index-1] if (0 <= index-1) else -np.inf
            high_edge = axis_binning[index] if (index < len(axis_binning)) else np.inf
            return low_edge, high_edge
        elif type(index) is slice:
            if index.step is not None:
                raise ValueError("step must be 1")
            return axis_binning[index.start], axis_binning[index.stop]
        elif type(index) is tuple:
            if len(index) != 2:
                raise ValueError("len must be 2")
            return (axis_binning[index[0]-1] if (0<=index[0]-1) else -np.inf,
                    axis_binning[index[1]] if (index[1] < len(axis_binning)) else np.inf)
        else:
            if inclusive_range:
                return axis_binning[0], axis_binning[-1]
            else:
                return None
                
    def axis_index(self, axis_name):
        """ return the index of the axis with axis_name """
        try:
            axis = self.axis_names.index(axis_name)
        except ValueError:
            raise ValueError("%s is not the name of an axis" % axis_name)
        return axis
    
    def middle_points(self, axis):
        if type(axis) == str:
            axis = self.axis_index(axis)
        axis = self.binnings[axis]
        return (axis[1:] + axis[:-1]) / 2
    
    def bin_widths(self, axis):
        if type(axis) == str:
            axis = self.axis_index(axis)
        axis = self.binnings[axis]
        return np.diff(axis)
    
    def __str__(self):
        result = []
        for b in self:
            result.append("%s (%s):\t %s" % (b["name"], b["title"], b["binning"]))
        for k, v in self.selection.iteritems():
            result.append("%s: \t (%f,%f)" % (k, v[0], v[1]))        
        return "\n".join(result)

    def directory_name(self, use_inclusive=True):
        if len(self.axis_names) == 0 and use_inclusive:
            return "inclusive"
        dir_name = '_'.join(self.axis_names)
        return dir_name
    
    
    def dim(self):
        """ the number of binning variables """
        return len(self.binnings)
    
    def digitize(self, values, axis):
        """
         digitize all values using only axis. axis can be also the name of the binning variable
         example: values = (0.1, 0.6)
                  axis = 0
                  --> [1, 2]
        """
        if type(axis) is str:
           axis = self.axis_index(axis) 
        return np.digitize(values, self.binnings[axis])
    
    def digitize_events(self, values):
        """
         digitize over all the axis, values must have the same dimensions of the number of axis
         example: values = [(0.1, 11), (0.6, 12)]
                       --> [[1, 1], [2, 1]]
        """
        values = np.array(values).transpose()
        return np.array([np.digitize(row, bins) for row, bins in zip(values, self.binnings)]).transpose()
    
    def bin_name(self, thebin, skip_inclusive=True, use_selection=True):
        """
        return the bin name. thebin counts from 0, 0 is the underflow
        with skip_inclusive=True if the input is ( ) it return "" else it will return the full range
        with use_selection=True it prepend the parent binning
        """
        if self.dim() != 0 and len(thebin) != self.dim():
            raise ValueError("bin dimension must be %d" % self.dim())
        elif self.dim() == 0 and (thebin != (0,) and thebin != ()):
            raise ValueError("bin must be (0,) for the inclusive case (%s) given" % str(thebin))
        result = []
        if use_selection: # prepend the selection
            for k, v in self.selection:
                result.append("%s%f-%f" % (k, v[0], v[1]))
        for info, b in zip(self, thebin):
            bin_name = info["name"]
            if type(b) is int:
                result.append("%s%d" % (bin_name, b))
            elif type(b) is slice:
                if b.step is not None:
                    raise ValueError("step must be 1")
                result.append("%s%d-%d" % (bin_name, b.start, b.stop))
            else:
                if skip_inclusive: continue
                result.append("%s" % bin_name)
        return "_".join(result)
    
    def pretty_bin_description(self, thebin, use_title=False, skip_inclusive=True, use_selection=True):
        name_key = "title" if use_title else "name"
        result = []
        if use_selection:
            for k, v in self.selection:
                result.append("%s%f-%f" % (k, v[0], v[1]))
        for info, b in zip(self, thebin):
            if b is not None:               
                bin_name = info[name_key]
                edges = self.get_range(bin_name, b)
                result.append("%s: [%.2f, %.2f]" % (bin_name, edges[0], edges[1]))
            else:
                if skip_inclusive: continue
                else:
                    bin_name = info[name_key]
                    result.append("%s: [inclusive]" % bin_name)                
        return " ".join(result)

def slugify(value):
    value = value.replace("/", "div").replace(".", "p")
    # from django project: https://code.djangoproject.com/browser/django/trunk/django/core/template/defaultfilters.py?rev=1443
    "Converts to lowercase, removes non-alpha chars and converts spaces to hyphens"
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('\s+', '-', value)

def powerset(iterable):
   "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
   s = list(iterable)
   return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def binning2array(binning):
    """Return binning as numpy.ndarray
    Input can be a dictionary with nbins, min, max or a list, tuple, etc
    """
    if isinstance(binning, np.ndarray):
        return binning
    elif isinstance(binning, dict):
        return np.linspace(binning['min'], binning['max'], binning['nbins']+1)
    else: # list, tuple, etc
        return np.asarray(binning)

def shift_bin(thebin, shift):
    if np.isscalar(shift):
        return (thebin + np.ones(len(thebin), dtype=np.int) * shift).tolist()
    elif len(thebin) == len(shift):
          return (thebin + np.array(shift)).tolist()
    else:
        raise ValueError("cannot shift, values have not the same size")
