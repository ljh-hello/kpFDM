import sys
import numpy as np
from scipy import rand
from scipy.sparse.linalg import eigsh, lobpcg
from scipy.sparse import lil_matrix, diags, block_diag, csr_matrix, bmat, kron
import matplotlib.pyplot as plt
import argparse
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
#from pyamg import smoothed_aggregation_solver

class UniversalConst(object):

    def __init__(self):
        """
        """
        self.RY = 13.6
        self.A0 = 0.529167
        self.eVAA2 = 3.67744
        self.planck = 6.58211928e-16 # ev*s
        self.m0 = 0.510998910e+6 #ev/c^2
        self.c = 299792458e+10 # AA/s
        self.hsqrO2m0 = (self.c**2)*(self.planck**2) / (2.*self.m0)

class DrawingFunctions(object):

   def __init__(self):
      """
      Parameters
      ----------
      dimen : integer
              system's dimensionality, i.e., quantum well, wire and dot
      """

   def square(self, params, profile, value, idx):
      """

      """

      if params['dimen'] == 1:

        profile[params['startPos'][idx]:params['endPos'][idx]] = value

      if params['dimen'] == 2:

        profile[params['startPos'][idx]:params['endPos'][idx],params['startPos'][idx]:params['endPos'][idx]] = value

      if params['dimen'] == 3:
         print 'Not implemented yet'


      return profile

class Potential(object):

    def __init__(self, params):
      """
      """

      # Set internal parameters

      if params['dimen'] == 1:
        if params['model'] == 'ZB2x2':
            self.pot = np.zeros(params['N'])
        if params['model'] == 'ZB6x6':
            self.pot = np.zeros(3*params['N']).reshape((3,params['N']))

      if params['dimen'] == 2:
        if params['model'] == 'ZB2x2':
            self.pot = np.zeros(params['N']**2).reshape(params['N'],params['N'])
        if params['model'] == 'ZB6x6':
            self.pot = np.zeros(3*params['N']**2).reshape((3,params['N'],params['N']))

    def buildPot(self, params, flag):
      """
      """
      drawFunc = DrawingFunctions()


      if params['potType'] == 'square':

          if params['model'] == 'ZB2x2':

              for i in range(params['nmat']):
                  #print 'constructing layer %d potential from %d(%f) to %d(%f)'%(i,params['startPos'][i],params['x'][params['startPos'][i]],
                  #params['endPos'][i],params['x'][params['endPos'][i]])

                  if flag == 'het':
                    value = params['gap'][0] + (params['gap'][i]-params['gap'][0])*(1.-params['bshift'])
                  if flag == 'kin':
                    value = params['elecmassParam'][i]

                  self.pot = drawFunc.square(params, self.pot, value, i)

          if params['model'] == 'ZB6x6':

              value = {}

              for i in range(params['nmat']):
                  #print 'constructing layer %d potential from %d(%f) to %d(%f)'%(i,params['startPos'][i],params['x'][params['startPos'][i]],
                  #params['endPos'][i],params['x'][params['endPos'][i]])

                  if flag == 'het':
                    value[0] = (params['gap'][0]-params['gap'][i])*params['bshift']
                    value[1] = value[0]
                    value[2] = value[0]-params['deltaSO'][i]
                  if flag == 'kin':
                    value[0] = params['gamma1'][i]
                    value[1] = params['gamma2'][i]
                    value[2] = params['gamma3'][i]

                  for j in range(3):
                    self.pot[j,:] = drawFunc.square(params, self.pot[j,:], value[j], i)

      else:
          print 'Not implemented yet'

      return self.pot


    def plotPot(self, params):
      """
      """
      UniConst = UniversalConst()
      fig = plt.figure()

      if params['model'] == 'ZB2x2':
        if params['dimen'] == 1:
          plt.plot(params['x']*UniConst.A0,self.pot)
          plt.show()
        if params['dimen'] == 2:
          ax = fig.gca(projection='3d')
          X, Y = np.meshgrid(params['x']*UniConst.A0, params['x']*UniConst.A0)
          surf = ax.plot_surface(X, Y, self.pot, rstride=1, cstride=1, cmap=cm.coolwarm,
                  linewidth=0, antialiased=False)

          ax.zaxis.set_major_locator(LinearLocator(10))
          ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

          fig.colorbar(surf, shrink=0.5, aspect=5)

          plt.show()
      if params['model'] == 'ZB6x6':
        plt.plot(params['x']*UniConst.A0,self.pot[0,:])
        plt.plot(params['x']*UniConst.A0,self.pot[1,:])
        plt.plot(params['x']*UniConst.A0,self.pot[2,:])
        plt.show()

class IO(object):

    def __init__(self):
        """
        """

        self.const = UniversalConst()
        self.parser = argparse.ArgumentParser(description='kp in real space by FDM')

        self.parameters = {}

        self.parse()

    def parse(self):
        """
        """
        self.parser.add_argument('-n','--NMAT',action='store', dest='nmat',
                                  type=int, help='Type: integer. Number of material which composes the system.')

        self.parser.add_argument('-d','--DIMEN',action='store', dest='dimen',
                                  type=int,
                                  help="""
                                  Type: integer. Dimensionality of the system, i.e.,
                                    1 -> quantum well,
                                    2 -> quantum wire,
                                    3 -> quantum dot.
                                    """)
        self.parser.add_argument('-m','--MODEL',action='store', dest='model',type=str,
                                 choices=['ZB2x2', 'ZB6x6', 'ZB8x8'], help="""
                                 Hamiltonian model: ZB2x2, ZB6x6, ZB8x8, WZ2x2, ....
                                 """)

        self.parser.add_argument('-p','--GAPS',action='store', dest='gap',
                                  type=float, nargs='+', help="""
                                  Material's gaps in the form: gap_material1, gap_material2, gap_material3, ... .
                                  Units of eV.
                                  """)

        self.parser.add_argument('-t','--type',action='store',dest='potType',
                                 type=str, help="""
                                 Potential type, i.e.,
                                 square, hexagon, circle, sphere, etc
                                 """)

        self.parser.add_argument('-s','--STARTPOS',action='store',dest='startPos',
                                  type=float, nargs='+', help="""
                                  Starting position of material: v1, v2, v3, ... .
                                  Units of Angstroms
                                  """)

        self.parser.add_argument('-e','--ENDPOS',action='store',dest='endPos',
                                  type=float, nargs='+', help="""
                                  Ending position of the band mismatch in the form: v1, v2, v3, ... .
                                  Units of Angstroms
                                  """)

        self.parser.add_argument('-st','--STEP',action='store',dest='step',type=float, help="""
                                 Discretization step in Angstrom
                                """)

        self.parser.add_argument('-dr','--DIRECTION',action='store',dest='direction',type=str, help="""
                                 Direction to compute the band structure, ex: kx, ky ou kz
                                """)

        self.parser.add_argument('-me','--ELECMASS',action='store',dest='elecmass',
                                  type=float, nargs='+', help="""
                                  Electron effective masses in the form: v1, v2, v3, ... .
                                  Units of m0. If WZ input e1 and e2 for all materials.
                                  """)

        self.parser.add_argument('-g1', '--gamma1',action='store',dest='gamma1',
                                  type=float, nargs='+', help="""
                                  Holes mass parameters in the form: gamma1, gamma1, ...
                                  """)

        self.parser.add_argument('-g2', '--gamma2',action='store',dest='gamma2',
                                  type=float, nargs='+', help="""
                                  Holes mass parameters in the form: gamma2, gamma2, ...
                                  """)

        self.parser.add_argument('-g3', '--gamma3',action='store',dest='gamma3',
                                  type=float, nargs='+', help="""
                                  Holes mass parameters in the form: gamma3, gamma3, ...
                                  """)

        self.parser.add_argument('-dso', '--DELTASO', action='store', dest='deltaSO',
                                  type=float, nargs='+', help="""
                                  Delta SO in the form: deltaso1, deltaso2, ...
                                  """)


        self.parser.add_argument('-lp','--LATPAR', action='store',dest='latpar',
                                  type=float, help="""
                                  General lattice parameter. Units of Angstrom
                                  """)

        self.parser.add_argument('-np', '--NPOINTS', action='store', dest='npoints',
                                  type=int, help="""
                                  Number of k points to compute
                                  """)

        self.parser.add_argument('-pc', '--PERCENTAGE', action='store', dest='percent',
                                  type=float, help="""
                                  Percentage of the k-mesh to compute
                                  """)

        self.parser.add_argument('-bs', '--BSHIFT', action='store', dest='shift',
                                  type=float, help="""
                                  Band shift in percentage for valance band, ex: 0.4
                                  """)

        self.parser.add_argument('-ncb', '--NUMCB', action='store', dest='numcb',
                                  type=int, help="""
                                  Number of conduction bands to compute
                                  """)

        self.parser.add_argument('-nvb', '--NUMVB', action='store', dest='numvb',
                                  type=int, help="""
                                  Number of valance bands to compute
                                  """)


        self.args = self.parser.parse_args()

        self.verification()

        self.buildParamDict()

    def verification(self):
        """
        """
        assert self.args.nmat > 1
        assert self.args.dimen >= 1
        assert (self.args.potType == 'square')

        assert self.args.model in ['ZB2x2', 'ZB6x6', 'ZB8x8']

        if self.args.model == 'ZB2x2':
          assert self.args.numcb > 0
        else:
          if self.args.model in ['ZB6x6', 'ZB8x8']:
            assert self.args.numvb > 0
            assert len(self.args.gamma1) == self.args.nmat
            assert len(self.args.gamma2) == self.args.nmat
            assert len(self.args.gamma3) == self.args.nmat
            assert len(self.args.deltaSO) == self.args.nmat


        if self.args.model in ['ZB2x2', 'ZB6x6', 'ZB8x8']:
            assert len(self.args.gap) == self.args.nmat
            if self.args.model in ['ZB2x2', 'ZB8x8']:
              assert len(self.args.elecmass) == self.args.nmat
        else:
            assert len(self.args.gap)/2 == self.args.nmat
            assert len(self.args.elecmass)/2 == self.args.nmat

        if self.args.dimen == 1:
          assert self.args.direction in ['kx', 'ky']
        else:
          assert self.args.direction in ['kz']

    def buildParamDict(self):
        """
        """

        # Primary parameters

        self.parameters['nmat'] = self.args.nmat
        self.parameters['dimen'] = self.args.dimen
        self.parameters['model'] = self.args.model
        self.parameters['potType'] = self.args.potType
        self.parameters['startPos'] = self.args.startPos
        self.parameters['endPos'] = self.args.endPos
        self.parameters['step'] = self.args.step
        self.parameters['direction'] = self.args.direction

        self.parameters['gap'] = self.args.gap
        self.parameters['elecmass'] = self.args.elecmass
        self.parameters['gamma1'] = self.args.gamma1
        self.parameters['gamma2'] = self.args.gamma2
        self.parameters['gamma3'] = self.args.gamma3
        self.parameters['deltaSO'] = self.args.deltaSO

        self.parameters['latpar'] = self.args.latpar
        self.parameters['npoints'] = self.args.npoints
        self.parameters['percentage'] = self.args.percent
        self.parameters['bshift'] = self.args.shift
        self.parameters['numcb'] = self.args.numcb
        self.parameters['numvb'] = self.args.numvb


        # Secondary parameters

        self.parameters['L'] = self.parameters['endPos'][0] - self.parameters['startPos'][0]
        self.parameters['Enorm'] = self.const.hsqrO2m0/(self.const.A0**2)

        if (self.parameters['endPos'][0]-self.parameters['startPos'][0])%self.parameters['step'] != 0:
          sys.exit("Discretization interval isnt divisible by total size, try another")
        else:
          self.parameters['N'] = (self.parameters['endPos'][0]-self.parameters['startPos'][0])/self.parameters['step']

        if self.parameters['dimen'] in [1, 2]:
            self.parameters['x'] = np.linspace(self.parameters['startPos'][0],self.parameters['endPos'][0],self.parameters['N'])
            self.parameters['x'] /= self.const.A0
        else:
            print 'Not implemented yet x'

        # Converting startPos and endPos to vector index

        startPos = np.zeros(self.parameters['nmat'])
        endPos = np.zeros(self.parameters['nmat'])

        if self.parameters['dimen'] in [1,2]:
            for i in range(self.parameters['nmat']):
              startPos[i] = abs(self.parameters['startPos'][0]-self.parameters['startPos'][i])/self.parameters['step']
              endPos[i] = startPos[0] + (self.parameters['endPos'][0]+self.parameters['endPos'][i])/self.parameters['step']
        else:
            print 'Not implemented yet dimen'

        self.parameters['startPos'] = [int(x) for x in startPos]
        self.parameters['endPos'] = [int(x) for x in endPos]

        # dimensionalization
        self.parameters['step'] /= self.const.A0
        if self.args.model in ['ZB2x2']:
          self.parameters['elecmassParam'] = [self.const.eVAA2/x for x in self.parameters['elecmass']]
        if self.args.model in ['ZB6x6']:
          self.parameters['gamma1'] = [self.const.eVAA2*x for x in self.parameters['gamma1']]
          self.parameters['gamma2'] = [self.const.eVAA2*x for x in self.parameters['gamma2']]
          self.parameters['gamma3'] = [self.const.eVAA2*x for x in self.parameters['gamma3']]


        return self.parameters



class ZincBlend(object):

   def __init__(self, params):
      """
      """

      self.const = UniversalConst()
      self.symmetry = 'cubic'
      self.N = int(params['N'])


      if params['dimen'] == 1:
        self.directbasis = np.array([params['latpar']/self.const.A0, params['latpar']/self.const.A0, 1. ])
      else:
        if params['dimen'] == 2:
          self.directbasis = np.array([ 1., 1., params['latpar']/self.const.A0])
        else:
            print 'Not implemented yet basis'

      # set Bravais basis in reciprocal space
      self.reciprocalbasis = 2.*np.pi/self.directbasis

      if params['dimen'] == 1:
        if params['direction'] == 'kx':
            kxlim = self.reciprocalbasis[0]*params['percentage']/100
            self.kmesh = np.linspace(0,kxlim,params['npoints'])
        if params['direction'] == 'ky':
            kylim = self.reciprocalbasis[1]*params['percentage']/100
            self.kmesh = np.linspace(0,kylim,params['npoints'])
      else:
        if params['dimen'] == 2:
          if params['direction'] == 'kz':
              kxlim = self.reciprocalbasis[2]*params['percentage']/100
              self.kmesh = np.linspace(0,kxlim,params['npoints'])
        else:
            print 'Not implemented yet mesh'


class ZBHamilton(ZincBlend):

    def __init__(self, params, potHet, Kin):
      """
      """

      ZincBlend.__init__(self,params)
      self.potHet = potHet
      self.Kin = Kin
      self.step = params['step']

    def buildHam2x2(self, params, kpoints):
      """
      """
      
      kx = kpoints[0]
      ky = kpoints[1]
      kz = kpoints[2]
      
      if params['dimen'] == 1:
  
        HT = csr_matrix((self.N,self.N), dtype=np.float64)
  
        A = diags(self.Kin,0)
  
        ksquare = kx**2 + ky**2
  
        # derivatives related terms
        nonlocal_diag = np.convolve(self.Kin,[1,2,1],'same')
        nonlocal_off = np.convolve(self.Kin,[1,1],'valid')
  
        nonlocal = (1./(2.*(self.step**2)))*(diags(nonlocal_diag,0) - diags(nonlocal_off,1) - diags(nonlocal_off,-1))
  
        HT = nonlocal + A*ksquare + diags(self.potHet,0)
  
        del nonlocal_diag
        del nonlocal_off
        del nonlocal
        del A
  
      if params['dimen'] == 2:
  
        HT = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
  
        diag = np.zeros((self.N-2)**2)
        offdiag1 = np.zeros((self.N-2)**2)
        diag2 = np.zeros((self.N-2)**2-self.N+2)
  
        ksquare = kz**2
  
        for i in range(1,self.N-1):
  
          diag[(i-1)*(self.N-2):i*(self.N-2)] = (1./(2.*self.step**2))*4.*self.Kin[1:self.N-1,i-1] +\
                                        (1./(2.*self.step**2))*np.convolve(self.Kin[:,i-1],[1,0,1],'valid') +\
                                        (1./(2.*self.step**2))*np.convolve(self.Kin[i-1,:],[1,0,1],'valid') +\
                                        self.Kin[1:self.N-1,i-1]*ksquare +\
                                        self.potHet[1:self.N-1,i-1]
  
          offdiag1[(i-1)*(self.N-2):i*(self.N-2)] = (1./(2.*self.step**2))*np.convolve(self.Kin[:,i-1],[1,1],'same')[1:self.N-1]
  
          if i < self.N-2:
            diag2[(i-1)*(self.N-2):i*(self.N-2)] = (1./(2.*self.step**2))*np.convolve(self.Kin[i-1,:],[1,1],'same')[1:self.N-1]
  
  
  
        HT.setdiag(diag,0)
        HT.setdiag(-offdiag1,1)
        HT.setdiag(-offdiag1,-1)
  
        HT.setdiag(-diag2,self.N)
        HT.setdiag(-diag2,-self.N)
  
        del diag
        del offdiag1
        del diag2
  
        #print 'HT is hermitian? ',np.allclose(HT.conjugate(), HT)
        #np.savetxt('HT.dat',HT.todense())
        
      return HT.tocsr()

    def buildHam6x6(self, params, kpoints):
      """
      """
      
      kx = kpoints[0]
      ky = kpoints[1]
      kz = kpoints[2]
      
      if params['dimen'] == 1:
    
        HT = lil_matrix((6*self.N,6*self.N), dtype=np.float64)
        
        Q      = lil_matrix((self.N,self.N), dtype=np.float64)
        T      = lil_matrix((self.N,self.N), dtype=np.float64)
        S      = lil_matrix((self.N,self.N), dtype=np.float64)
        SC     = lil_matrix((self.N,self.N), dtype=np.float64)
        R      = lil_matrix((self.N,self.N), dtype=np.float64)
        RC     = lil_matrix((self.N,self.N), dtype=np.float64)
        ZERO   = lil_matrix((self.N,self.N), dtype=np.float64)
        gamma1 = lil_matrix((self.N,self.N), dtype=np.float64)
        gamma2 = lil_matrix((self.N,self.N), dtype=np.float64)
        gamma3 = lil_matrix((self.N,self.N), dtype=np.float64)
        
        gamma1.setdiag(self.Kin[0,:],0)
        gamma2.setdiag(self.Kin[1,:],0)
        gamma3.setdiag(self.Kin[2,:],0)
        
        # Q
        nonlocal_diag = np.convolve(self.Kin[0,:] - 2.*self.Kin[1,:],[1,2,1],'same')
        nonlocal_off = np.convolve(self.Kin[0,:] - 2.*self.Kin[1,:],[1,1],'valid')
        
        Q.setdiag(nonlocal_diag,0)
        Q.setdiag(-nonlocal_off,1)
        Q.setdiag(-nonlocal_off,-1)
        Q *= (1./(2.*self.step**2))
        Q += ( (gamma1+gamma2)*(kx**2 + ky**2) )
        Q *= -1.
        
        #np.savetxt('Q.dat',Q.todense())
        
        # T
        nonlocal_diag = np.convolve(self.Kin[0,:]+2.*self.Kin[1,:],[1,2,1],'same')
        nonlocal_off = np.convolve(self.Kin[0,:]+2.*self.Kin[1,:],[1,1],'valid')
        
        T.setdiag(nonlocal_diag,0)
        T.setdiag(-nonlocal_off,1)
        T.setdiag(-nonlocal_off,-1)
        T *= (1./(2.*self.step**2))
        T += ( (gamma1-gamma2)*kx**2 + (gamma1-gamma2)*ky**2 )
        T *= -1.
        
        #np.savetxt('T.dat',T.todense())
        
        # S
        nonlocal_off = (1./(4.*self.step))*np.convolve(self.Kin[2,:],[1,1],'valid')
        
        S.setdiag(-nonlocal_off,1)
        S.setdiag(nonlocal_off,-1)
        S*=2.*np.sqrt(3.)*complex(kx,ky)
        SC.setdiag(nonlocal_off,1)
        SC.setdiag(-nonlocal_off,-1)
        SC*=2.*np.sqrt(3.)*complex(kx,-ky)
        
        #np.savetxt('S.dat',S.todense())
        
        # R
        R = -2.*np.sqrt(3.)*(gamma2*(kx**2 + ky**2)-complex(0,1.)*gamma3*kx*ky)
        RC = -2.*np.sqrt(3.)*(gamma2*(kx**2 + ky**2)+complex(0,1.)*gamma3*kx*ky)
        
        #np.savetxt('R.dat',R.todense())
        
        IU = complex(0,1.)
        sqr2 = np.sqrt(2.)
        rqs2 = 1./np.sqrt(2.)
        sqr3 = np.sqrt(3.)
        
        HT += kron(Q          ,[[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(S          ,[[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(R          ,[[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(ZERO       ,[[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*rqs2*S  ,[[0,0,0,0,1,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*sqr2*R ,[[0,0,0,0,0,1],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(SC             ,[[0,0,0,0,0,0],[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(T              ,[[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(ZERO           ,[[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(R              ,[[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*rqs2*(Q-T) ,[[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*sqr3*rqs2*S ,[[0,0,0,0,0,0],[0,0,0,0,0,1],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(RC               ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(ZERO             ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(T                ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-S               ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*sqr3*rqs2*SC ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*rqs2*(Q-T)   ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(ZERO        ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(RC          ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-SC         ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(Q           ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*sqr2*RC ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*rqs2*SC ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(-IU*rqs2*SC    ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[1,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*rqs2*(Q-T)  ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*sqr3*rqs2*S ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*sqr2*R      ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(.5*(Q+T)       ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(ZERO           ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(IU*sqr2*RC       ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[1,0,0,0,0,0]], format='lil')
        HT += kron(-IU*sqr3*rqs2*SC ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,1,0,0,0,0]], format='lil')
        HT += kron(IU*rqs2*(Q-T)    ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0]], format='lil')
        HT += kron(IU*rqs2*S        ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0]], format='lil')
        HT += kron(ZERO             ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0]], format='lil')
        HT += kron(0.5*(Q+T)        ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1]], format='lil')
        
        HT += kron(diags(self.potHet[0,:],0) ,[[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(diags(self.potHet[1,:],0) ,[[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(diags(self.potHet[1,:],0) ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(diags(self.potHet[0,:],0) ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(diags(self.potHet[2,:],0) ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(diags(self.potHet[2,:],0) ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1]], format='lil')
      
        del Q     
        del T     
        del S     
        del SC    
        del R     
        del RC    
        del ZERO  
        del gamma1
        del gamma2
        del gamma3
        del nonlocal_diag
        del nonlocal_off
        del nonlocal
      
      if params['dimen'] == 2:
        
        
        HT = lil_matrix((6*(self.N-2)**2,6*(self.N-2)**2), dtype=np.float64)
        
        Q      = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
        diagQ     = np.zeros((self.N-2)**2)
        offdiagQ = np.zeros((self.N-2)**2)
        diag2Q    = np.zeros((self.N-2)**2-self.N+2)
        
        T      = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
        diagT     = np.zeros((self.N-2)**2)
        offdiagT = np.zeros((self.N-2)**2)
        diag2T = np.zeros((self.N-2)**2-self.N+2)
        
        S      = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
        offdiagS = np.zeros((self.N-2)**2)
        offdiag2S = np.zeros((self.N-2)**2-self.N+2)
        SC     = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
        
        R      = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
        diagR     = np.zeros((self.N-2)**2)
        offdiagR = np.zeros((self.N-2)**2)
        diag2R = np.zeros((self.N-2)**2-self.N+2)        
        diagR2     = np.zeros((self.N-2)**2)
        offdiagR2 = np.zeros((self.N-2)**2)
        diag2R2 = np.zeros((self.N-2)**2-self.N+2)
        RC     = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
        
        ZERO   = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
      
        QpT = lil_matrix(((self.N-2)**2,(self.N-2)**2), dtype=np.float64)
        diagQpT = np.zeros((self.N-2)**2)
        
        
        gamma1 = self.Kin[0,:]
        gamma2 = self.Kin[1,:]
        gamma3 = self.Kin[2,:]
        
        ksquare = kz**2
        
        for i in range(1,self.N-1):
          
          auxQ = gamma1 - 2.*gamma2
          auxT = gamma1 + 2.*gamma2
          
          diagQ[(i-1)*(self.N-2):i*(self.N-2)] = -(1./(2.*self.step**2))*4.*(auxQ[1:self.N-1,i-1])-\
                              (1./(2.*self.step**2))*np.convolve(auxQ[:,i-1],[1,0,1],'valid') -\
                              (1./(2.*self.step**2))*np.convolve(auxQ[i-1,:],[1,0,1],'valid') -\
                              (gamma1[1:self.N-1,i-1]+gamma2[1:self.N-1,i-1])*ksquare
                              
                              
          diagT[(i-1)*(self.N-2):i*(self.N-2)] = -(1./(2.*self.step**2))*4.*(auxT[1:self.N-1,i-1])-\
                              (1./(2.*self.step**2))*np.convolve(auxT[:,i-1],[1,0,1],'valid') -\
                              (1./(2.*self.step**2))*np.convolve(auxT[i-1,:],[1,0,1],'valid') -\
                              (gamma1[1:self.N-1,i-1]-gamma2[1:self.N-1,i-1])*ksquare
                              
                              
          diagQpT = 0.5*(diagQ[(i-1)*(self.N-2):i*(self.N-2)] + diagT[(i-1)*(self.N-2):i*(self.N-2)]) +\
                    self.potHet[2,1:self.N-1,i-1]

          diagQ[(i-1)*(self.N-2):i*(self.N-2)] += self.potHet[0,1:self.N-1,i-1]
          diagT[(i-1)*(self.N-2):i*(self.N-2)] += self.potHet[1,1:self.N-1,i-1]

          diagR[(i-1)*(self.N-2):i*(self.N-2)] = -(1./(2.*self.step**2))*np.convolve(gamma2[:,i-1],[1,0,1],'valid') +\
                              (1./(2.*self.step**2))*np.convolve(gamma2[i-1,:],[1,0,1],'valid')

          diagR2[(i-1)*(self.N-2):i*(self.N-2)] = complex(0.,1.)*((1./(self.step**2))*4.*(gamma3[1:self.N-1,i-1]) +\
                              (1./(self.step**2))*np.convolve(gamma3[:,i-1],[1,0,1],'valid') +\
                              (1./(self.step**2))*np.convolve(gamma3[i-1,:],[1,0,1],'valid'))

                              
          offdiagQ[(i-1)*(self.N-2):i*(self.N-2)] = -(1./(2.*self.step**2))*np.convolve(auxQ[:,i-1],[1,1],'same')[1:self.N-1]
          offdiagT[(i-1)*(self.N-2):i*(self.N-2)] = -(1./(2.*self.step**2))*np.convolve(auxT[:,i-1],[1,1],'same')[1:self.N-1]
          offdiagS[(i-1)*(self.N-2):i*(self.N-2)] = (1./(4.*self.step))*np.convolve(gamma3[:,i-1],[1,1],'same')[1:self.N-1]
          offdiagR[(i-1)*(self.N-2):i*(self.N-2)] = (1./(2.*self.step**2))*np.convolve(gamma2[:,i-1],[1,1],'same')[1:self.N-1]
          offdiagR2[(i-1)*(self.N-2):i*(self.N-2)] = complex(0.,-1.)*(1./(self.step**2))*np.convolve(gamma3[i-1,:],[1,1],'same')[1:self.N-1]

          if i < self.N-2:
            diag2Q[(i-1)*(self.N-2):i*(self.N-2)] = -(1./(2.*self.step**2))*np.convolve(auxQ[i-1,:],[1,1],'same')[1:self.N-1]
            diag2T[(i-1)*(self.N-2):i*(self.N-2)] = -(1./(2.*self.step**2))*np.convolve(auxT[i-1,:],[1,1],'same')[1:self.N-1]
            offdiag2S[(i-1)*(self.N-2):i*(self.N-2)] = (1./(4.*self.step))*np.convolve(gamma3[i-1,:],[1,1],'same')[1:self.N-1]
            diag2R[(i-1)*(self.N-2):i*(self.N-2)] = -(1./(2.*self.step**2))*np.convolve(gamma2[i-1,:],[1,1],'same')[1:self.N-1]
            diag2R2[(i-1)*(self.N-2):i*(self.N-2)] = complex(0.,-1.)*(1./(self.step**2))*np.convolve(gamma3[:,i-1],[1,1],'same')[1:self.N-1]

        Q.setdiag(diagQ,0)
        Q.setdiag(-offdiagQ,1)
        Q.setdiag(-offdiagQ,-1)
        Q.setdiag(-diag2Q,self.N)
        Q.setdiag(-diag2Q,-self.N)
        
        T.setdiag(diagT,0)
        T.setdiag(-offdiagT,1)
        T.setdiag(-offdiagT,-1)
        T.setdiag(-diag2T,self.N)
        T.setdiag(-diag2T,-self.N)
        
        QpT.setdiag(diagQpT,0)
        QpT.setdiag(-0.5*(offdiagQ+offdiagT),1)
        QpT.setdiag(-0.5*(offdiagQ+offdiagT),-1)
        QpT.setdiag(-0.5*(diag2Q+diag2T),self.N)
        QpT.setdiag(-0.5*(diag2Q+diag2T),-self.N)
        
        S.setdiag(offdiagS,1)
        S.setdiag(-offdiagS,-1)
        S.setdiag(complex(0.,-1.)*offdiag2S,self.N+1)
        S.setdiag(-complex(0.,-1.)*offdiag2S,-self.N-1)
        S*=2.*np.sqrt(3.)*kz
        
        SC.setdiag(-offdiagS,1)
        SC.setdiag(offdiagS,-1)
        SC.setdiag(-complex(0.,1.)*offdiag2S,self.N+1)
        SC.setdiag(complex(0.,1.)*offdiag2S,-self.N-1)
        SC*=2.*np.sqrt(3.)*kz
        
        R.setdiag(diagR + diagR2, 0)
        R.setdiag(offdiagR + offdiagR2,1)
        R.setdiag(offdiagR + offdiagR2,-1)
        R.setdiag(diag2R + diag2R2,self.N)
        R.setdiag(diag2R + diag2R2,-self.N)
        R*=2.*np.sqrt(3.)
        
        RC.setdiag(diagR - diagR2, 0)
        RC.setdiag(offdiagR - offdiagR2,1)
        RC.setdiag(offdiagR - offdiagR2,-1)
        RC.setdiag(-diag2R - diag2R2,self.N)
        RC.setdiag(-diag2R - diag2R2,-self.N)
        RC*=2.*np.sqrt(3.)
        
        IU = complex(0,1.)
        sqr2 = np.sqrt(2.)
        rqs2 = 1./np.sqrt(2.)
        sqr3 = np.sqrt(3.)
        
        HT += kron(Q          ,[[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(S          ,[[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(R          ,[[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(ZERO       ,[[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*rqs2*S  ,[[0,0,0,0,1,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*sqr2*R ,[[0,0,0,0,0,1],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(SC             ,[[0,0,0,0,0,0],[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(T              ,[[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(ZERO           ,[[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(R              ,[[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*rqs2*(Q-T) ,[[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*sqr3*rqs2*S ,[[0,0,0,0,0,0],[0,0,0,0,0,1],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(RC               ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(ZERO             ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(T                ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-S               ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*sqr3*rqs2*SC ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*rqs2*(Q-T)   ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(ZERO        ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[1,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(RC          ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-SC         ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(Q           ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*sqr2*RC ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(-IU*rqs2*SC ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1],[0,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(-IU*rqs2*SC    ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[1,0,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*rqs2*(Q-T)  ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*sqr3*rqs2*S ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(IU*sqr2*R      ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(QpT            ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0],[0,0,0,0,0,0]], format='lil')
        HT += kron(ZERO           ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1],[0,0,0,0,0,0]], format='lil')
        
        HT += kron(IU*sqr2*RC       ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[1,0,0,0,0,0]], format='lil')
        HT += kron(-IU*sqr3*rqs2*SC ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,1,0,0,0,0]], format='lil')
        HT += kron(IU*rqs2*(Q-T)    ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,1,0,0,0]], format='lil')
        HT += kron(IU*rqs2*S        ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,1,0,0]], format='lil')
        HT += kron(ZERO             ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,1,0]], format='lil')
        HT += kron(QpT              ,[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,1]], format='lil')

      return HT.tocsr()
      
    def buildHam(self, params, kpoints):
      """
      """

      if params['model'] == 'ZB2x2':

        HT = self.buildHam2x2(params, kpoints)

      if params['model'] == 'ZB6x6':

        HT = self.buildHam6x6(params, kpoints)

      return HT.tocsr()


    def solve(self,params):
      """
      """

      if params['model'] == 'ZB2x2':
        va = np.zeros(int(params['npoints'])*int(params['numcb'])).reshape((int(params['numcb']),int(params['npoints'])))

        if params['dimen'] == 1:
          ve = np.zeros(int(params['npoints'])*int(params['numcb'])*int(params['N'])).reshape((int(params['N']),int(params['numcb']),int(params['npoints'])))
          X = np.zeros(int(params['numcb'])*int(params['N'])).reshape((int(params['N']),int(params['numcb'])))
          X = rand(int(params['N']),int(params['numcb']))

        if params['dimen'] == 2:
          ve = np.zeros(int(params['npoints'])*int(params['numcb'])*int(params['N']-2)**2).reshape((int(params['N']-2)**2,int(params['numcb']),int(params['npoints'])))
          X = np.zeros(int(params['numcb'])*int(params['N']-2)**2).reshape((int(params['N']-2)**2,int(params['numcb'])))
          X = rand(int(params['N']-2)**2,int(params['numcb']))

      if params['model'] == 'ZB6x6':
        va = np.zeros(int(params['npoints'])*int(params['numvb'])).reshape((int(params['numvb']),int(params['npoints'])))
        
        if params['dimen'] == 1:
          ve = np.zeros(int(params['npoints'])*int(params['numvb'])*6*(int(params['N']))).reshape((6*(int(params['N'])),int(params['numvb']),int(params['npoints'])))

        if params['dimen'] == 2:
          ve = np.zeros(int(params['npoints'])*int(params['numvb'])*6*int(params['N']-2)**2).reshape((6*int(params['N']-2)**2,int(params['numvb']),int(params['npoints'])))


      for i in range(int(params['npoints'])):

        if params['direction'] == 'kx':
          kpoints = np.array([self.kmesh[i],0,0])
        if params['direction'] == 'ky':
          kpoints = np.array([0,self.kmesh[i],0])
        if params['direction'] == 'kz':
          kpoints = np.array([0,0,self.kmesh[i]])

        print "Solving k = ",kpoints/self.const.A0

        HT = self.buildHam(params,kpoints)
        HT /= params['Enorm']

        if params['model'] == 'ZB2x2':
          va[:,i], ve[:,:,i] = eigsh(HT, int(params['numcb']), which='SM')
          #va[:,i], ve[:,:,i] = lobpcg(HT,X,M=None,largest=False,tol=1e-5,verbosityLevel=1, maxiter=400)

        if params['model'] == 'ZB6x6':
          va[:,i], ve[:,:,i] = eigsh(HT, int(params['numvb']), which='LA')
          #va[:,i], ve[:,:,i] = lobpcg(HT,X,M=None,largest=True,tol=1e-5,verbosityLevel=0, maxiter=400)

        if params['model'] == 'ZB8x8':
          print 'Not implemented yet'

      return self.kmesh, va, ve


#===============================================


UniConst = UniversalConst()
ioObject = IO()

#print ioObject.parameters['N']


# Building potential
P = Potential(ioObject.parameters)
pothet = P.buildPot(ioObject.parameters,'het')

# Building effective mass variation
K = Potential(ioObject.parameters)
kin = K.buildPot(ioObject.parameters,'kin')

P.plotPot(ioObject.parameters)
#K.plotPot(ioObject.parameters)
#sys.exit()

# Set parameters to Hamiltonian
ZB = ZBHamilton(ioObject.parameters, pothet, kin)

k, va, ve = ZB.solve(ioObject.parameters)

print va*ioObject.parameters['Enorm']


if ioObject.parameters['model'] == 'ZB2x2':

  fig = plt.figure()
  for i in range(ioObject.parameters['numcb']):
    plt.plot(k/UniConst.A0, va[i,:]*ioObject.parameters['Enorm'])
  plt.show()

"""
  fig = plt.figure()
  ax = fig.gca(projection='3d')
  X, Y = np.meshgrid(ioObject.parameters['x'][1:ioObject.parameters['N']-1]*UniConst.A0, ioObject.parameters['x'][1:ioObject.parameters['N']-1]*UniConst.A0)
  surf = ax.plot_surface(X, Y, ve1[:,:,0,0]**2 , rstride=1, cstride=1, cmap=cm.coolwarm,
          linewidth=0, antialiased=False)

  ax.zaxis.set_major_locator(LinearLocator(10))
  ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

  fig.colorbar(surf, shrink=0.5, aspect=5)

  plt.show()

  fig = plt.figure()
  ax = fig.gca(projection='3d')

  surf = ax.plot_surface(X, Y, ve1[:,:,1,0]**2 , rstride=1, cstride=1, cmap=cm.coolwarm,
          linewidth=0, antialiased=False)

  ax.zaxis.set_major_locator(LinearLocator(10))
  ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

  fig.colorbar(surf, shrink=0.5, aspect=5)

  plt.show()

  fig = plt.figure()
  ax = fig.gca(projection='3d')

  surf = ax.plot_surface(X, Y, ve1[:,:,2,0]**2 , rstride=1, cstride=1, cmap=cm.coolwarm,
          linewidth=0, antialiased=False)

  ax.zaxis.set_major_locator(LinearLocator(10))
  ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

  fig.colorbar(surf, shrink=0.5, aspect=5)

  plt.show()
"""


if ioObject.parameters['model'] == 'ZB6x6':

  fig = plt.figure()
  for i in range(int(ioObject.parameters['numvb'])):
    plt.plot(k/UniConst.A0, va[i,:]*ioObject.parameters['Enorm'])
    plt.plot(-k/UniConst.A0, va[i,:]*ioObject.parameters['Enorm'])
  plt.show()


