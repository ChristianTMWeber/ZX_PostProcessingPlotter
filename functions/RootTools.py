import ROOT, numpy as np, itertools, array, os
#from performance import memoize
from performanceTools import memoized, binning2array
ROOT.PyConfig.IgnoreCommandLineOptions = True

ROOT.TH1.AddDirectory(0)

import logging

@memoized
def FixEstimate(tree):
    """Call tree.SetEstimate(N * tree.GetEntries() ) to avoid problems with TTree::Draw
    N is the maximum number of variables X the maximum depth (say 10)"""
    N = 2 if tree.GetEntries() > 10e6 else 10
    tree.SetEstimate( N * tree.GetEntries())

def GetValuesFromTree(tree, variable, cut = '', flatten=True, nevents=None, dtype=float, forceMultidim=False):
    """
    adapted from PyH4l of B. Lenzi
    GetValuesFromTree(tree, variable, cut) -> 
    Return a ndarray with <variable> which can be single or multi-dimensional
    """
    def GetNdim(tree):
        "Return the dimension of the last expression used with TTree::Draw"
        for i in xrange(100):
            if not tree.GetVar(i):
                return i
    
    def GetData(tree, i, N, dtype=float):
      "Return a ndarray from the i-th expression used with TTree::Draw"
      data = tree.GetVal(i)
      data.SetSize(N)
      return np.fromiter(data, dtype=dtype)
    
    t = tree #tree.Clone()
    FixEstimate(tree)
    if nevents is not None:
        N = t.Draw(variable, cut, 'goff', nevents)
    else:
        N = t.Draw(variable, cut, 'goff')
    Ndim = GetNdim(t)
    if Ndim == 0:
        raise ValueError("problem with formula %s or cut %s with file %s" % (variable, cut, t.GetCurrentFile().GetName()))
    if Ndim > 4: # beyond ROOT limit, workaround
      variables = [t.GetVar(i).GetTitle() for i in range(Ndim)] # TTreeFormula
      split_vars = [':'.join(variables[i:i+4]) for i in range(0, Ndim, 4)]
      print 'Splitting into pieces of 4 variables and concatenating: %s' % split_vars
      # Force each array to be multidimensional, even if Ndim = 1
      return np.concatenate([GetValuesFromTree(tree, v, cut, flatten, nevents, dtype, True) for v in split_vars])

    if Ndim == 1 and not forceMultidim:
        return GetData(t, 0, N, dtype)
    elif flatten:
        return np.ravel([GetData(t, i, N, dtype) for i in range(Ndim)])
    else:
        return np.array([GetData(t, i, N, dtype) for i in range(Ndim)])


def GetValuesFromTreeWithProof(tree, variable, cut = '', flatten=False, is1D = False, 
  doSort=True):
  """GetValuesFromTreeWithProof(tree, variable, cut = '', flatten=False, is1D = False)
  Use proof to load branches. Works just like GetValuesFromTree but
  2 subsequent calls will not have aligned values in general"""
  if not is1D and ':' not in variable.replace('::', ''): 
    # FIXME: this is correct in general (e.g: a > 0 ? 1 : 0)
    variable = '1:' + variable # Draw in 1D case would produce a TH1, we need a TGraph
    is1D = True
  if doSort and is1D:
    variable = 'Entry$:' + variable[2:]
  if not hasattr(ROOT, 'gProof'):
    proof = ROOT.TProof.Open('')
  if not isinstance(tree, ROOT.TChain):
    logging.info('Converting tree to TChain')
    chain = ROOT.TChain(tree.GetName())
    chain.Add(tree.GetDirectory().GetName())
    tree = chain
  tree.SetProof(True)
  N = tree.Draw(variable, cut)
  output = ROOT.gProof.GetOutputList()[2]
  if isinstance(output, ROOT.TGraph):
    # 1D or 2D case
    y = output.GetX() # Draw(a:b) gives (b,a) plot
    y.SetSize(N)
    if is1D and not doSort:
      return np.array(y)
    else:
      x = output.GetY()
      x.SetSize(N)
      if is1D and doSort:
        a = np.array(y)
        print 'Sorting entries...'
        return a[np.argsort(x)]
      a = np.array([x,y])
  elif isinstance(output, ROOT.TPolyMarker3D):
    # 3D case
    x = output.GetP()
    x.SetSize(3*N)
    # output gives z,y,x values alternated
    a = np.array(x).reshape(N, 3).T
    # z,y,x -> x, y, z
    a = np.flipud(a)
  else:
    raise ValueError('Unrecognised output: %s' % output)
  if flatten:
    return np.ravel(a)
  return a

    
def getArray(x):
    "Return array.array given a list or numpy.ndarray"
#     if isinstance(x, np.ndarray):
#         return x
    try:
        return array.array('f', x)
    except Exception as err:
        raise err("Got %s" % str(x))

def getHisto(binning, iclass = ROOT.TH1F, **kw):
  "getHisto(binning, iclass = ROOT.TH1F, **kw) -> ROOT histogram (TH1-3, TProfile, ...)"
  bins = []
  kw['binning'] = binning2array(binning)
  for i in 'binning', 'ybinning', 'zbinning':
      if i in kw:
          x = binning2array(kw.pop(i))
          bins.extend( [len(x) - 1, getArray(x) if iclass is not ROOT.TProfile2D else x] )
  h = iclass('h', '', *bins) # name and title can be changed later
  formatHisto(h, **kw)
  return h

histoFormatMethods = dict(
  name = lambda x, y: x.SetName(y),
  title = lambda x, y: x.SetTitle(y),
  xtitle = lambda x,y: x.GetXaxis().SetTitle(y),
  ytitle = lambda x,y: x.GetYaxis().SetTitle(y),
  ztitle = lambda x,y: x.GetZaxis().SetTitle(y),
  minimum = lambda x,y: x.SetMinimum(y),
  maximum = lambda x,y: x.SetMaximum(y),
  buildOptions = lambda x,y: x.BuildOptions(*y),
  markercolor = lambda x,y: x.SetMarkerColor(y),
  markersize = lambda x,y: x.SetMarkerSize(y),
)

def formatHisto(histo, **kw):
  "formatHisto(histo, **kw) --> Format ROOT histogram (name, title, xtitle, ...)"
  for k,v in kw.iteritems():
      if k in histoFormatMethods and v is not None:
          histoFormatMethods[k](histo, v)


@memoized
def getHistoBinning(histo):
  "Return an iterable with the bin edges of the given TH1"
  ax = histo.GetXaxis()
  if ax.GetXbins().GetSize():
    return itertools.imap(ax.GetXbins().__getitem__, xrange(ax.GetXbins().GetSize()) )
  else:
    return np.linspace(ax.GetXmin(), ax.GetXmax(), ax.GetNbins()+1)

## Compile C++ filler code
#try:
#  filler = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../test/filler.C')
#  ROOT.gROOT.LoadMacro(filler)
#except Exception as e:
#  print 'Could not load C++ filler: %s(%s)' % (e.__class__.__name__, e.message)

def fill(histo, *values):
  """fill(histo, *values) -> fill histo (TH1-3, TProfile, TProfile2D) using C++ code.
  Each element in <values> has to map to Float_t*. Hint: try to call np.array( v )"""
  ROOT.fill(histo, len(values[0]), *values)



def fillHistoWithNumpy(data, binning, weights = None, iclass=ROOT.TH1F, histo_name = "h",UF=False,OF=False):
    "Fill histogram with numpy --> fillHistoWithNumpy(data, binning, weights = None, iclass=ROOT.TH1F, histo_name = 'h',UF=False,OF=False)"
    # TO BRUNO: Why don't use the binning of the histogram?
    # binnig can be a list or np.array, of type int or float
    if not len(binning):
        raise ValueError('binning array is empty')
    bincount = np.histogram(data, binning, weights = weights)[0]
    histo = getHisto(binning[0 if not UF else 1:None if not OF else -1], iclass)
    histo.SetName(histo_name)
    histo.SetTitle(histo_name)
    for i,j in enumerate(bincount):
        histo.SetBinContent(i+(0 if UF else 1), j)
    #list( itertools.starmap(histo.SetBinContent, enumerate(bincount) ) )

    l = len(data)
    histo.SetEntries(l) # TO BRUNO: bug fixed, this must be after the SetBinContent method
                                  # every SetBinContent call increase the GetEntries() by 1
    stats = array.array('d', [l, l, np.sum(data), np.sum(np.square(data))])
    histo.PutStats(stats)

    return histo


class RootHistoGetter(object):
    "To get one or a numpy.ndarray of TH1s: RootHistoGetter(binning)(data)"
    def __init__(self, binning, iclass = ROOT.TH1F, filler = fillHistoWithNumpy, **kw):
        self.histo = getHisto(binning, iclass, **kw)
  
    def __call__(self, *data):
        if len(data) and len(data[0]):
            h = self.histo.Clone()
            fill(h, *(i for i in data if i is not None) )
            return h
        return self.histo

def getGraph(x, y, e=None, ey=None):
  """getGraph(x, y, e=None, ey=None):
  Return a TGraph (if e = None) or TGraphErrors built from the iterables x,y, e, ey
  <e> is assumed to be the error on y except if both <e> and <ey> are specified"""
  N = len(x)
  if N == 0:
      logging.warning("empy values from graph")
      return ROOT.TGraphErrors()
  if e is None: # no errors
    g = ROOT.TGraph( N, getArray(x), getArray(y) )
  elif ey is None: # errors on the y axis only
    g = ROOT.TGraphErrors( N, *map(getArray, (x, y, np.zeros(N), e)) )
  else:
    g = ROOT.TGraphErrors( N, *map(getArray, (x, y, e, ey)) )
  for i,j in reversed(list(enumerate(np.isfinite(y)))): # remove nan and inf
    if not j: g.RemovePoint(i)
  return g  


def getTH2(xbinning, ybinning, iclass=ROOT.TH2F, **kw):
  "getTH2(xbinning, ybinning) --> Return a TH2"
  return getHisto(xbinning, iclass, ybinning=ybinning, **kw)

def fillTH2fromMatrix(histo, M):
  "Fill a TH2 with the values from the matrix M"
  # TODO: fix in case of under/overflows
  [histo.SetBinContent(i+1, j+1, k) for i,a in enumerate(M) for j,k in enumerate(a)]
  return histo

class Root2DHistoGetter(object):
  "To get and fill a TH2 using a matrix: Root2DHistoGetter(xbinning, ybinning)(M)"
  def __init__(self, xbinning, ybinning, **kw):
    self.histo = getTH2(xbinning, ybinning, **kw)
  
  def __call__(self, *values):
    histo = self.histo.Clone()
    if len(values) == 1: # assume it is a matrix
      return fillTH2fromMatrix(histo, values[0])
    if len(values):
      fill(histo, *values)
    return histo
#     return fillTH2fromMatrix(self.histo.Clone(), M) # --> Sometimes it becomes TGraphErrors!!!


def correctionGenerator(input_tree, fcn, branches, default_value = None):
    """correctionGenerator(input_tree, fcn, branches) -> generator to calculate
    fcn(*branches) for each event in a TTree. The input branches can be single values
    or iterables (vectors)"""
    for i in xrange( input_tree.GetEntries() ):
        input_tree.GetEntry(i)
        try:
            inputs = map(input_tree.__getattr__, branches)
        except AttributeError:
            yield default_value
        try:
            yield fcn(*inputs)
        except TypeError:
            yield [fcn(*i) for i in itertools.izip(*inputs)]


def hLine(y, x1=None, x2=None, fix_histo=None):
  "hLine(y, x1=None, x2=None, fix_histo=None) -> horizontal line" 
  frame = ROOT.gPad.GetFrame()
  if x1 is None:
    x1 = frame.GetX1() if not ROOT.gPad.GetLogx() else 10**frame.GetX1()
  if x2 is None:
    x2 = frame.GetX2() if not ROOT.gPad.GetLogx() else 10**frame.GetX2()
  if fix_histo:
    # Fix the axis range to make sure that the line appears
    min_axis_y = frame.GetY1()
    max_axis_y = frame.GetY2()
    y1 = min(min_axis_y, y - (max_axis_y - min_axis_y) * 0.05)
    y2 = max(max_axis_y, y + (max_axis_y - min_axis_y) * 0.05)
    fix_histo.GetYaxis().SetRangeUser(y1, y2)
  return ROOT.TLine(x1, y, x2, y)

def vLine(x, y1=None, y2=None, fix_histo=None):
  "vLine(x, y1=None, y2=None) -> vertical line" 
  frame = ROOT.gPad.GetFrame()
  if y1 is None:
    y1 = frame.GetY1() if not ROOT.gPad.GetLogy() else 10**frame.GetY1()
  if y2 is None:
    y2 = frame.GetY2() if not ROOT.gPad.GetLogy() else 10**frame.GetY2()
  if fix_histo:
    # Fix the axis range to make sure that the line appears
    min_axis_x = frame.GetX1()
    max_axis_x = frame.GetX2()
    x1 = min(min_axis_x, x - (max_axis_x - min_axis_x) * 0.05)
    x2 = max(max_axis_x, x + (max_axis_x - min_axis_x) * 0.05)
    fix_histo.GetYaxis().SetRangeUser(x1, x2)
  return ROOT.TLine(x, y1, x, y2)
