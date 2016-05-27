# -*- coding: utf-8 -*-
"""
source - Module for seismic sources modeling.

This module provides class hierarchy for earthquake modeling and 
 representation.
______________________________________________________________________

.. note::    
    
    Functions and classes are ordered from general to specific.

"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from obspy.imaging.scripts.mopad import MomentTensor


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    
    v = [3, 5, 0]
	axis = [4, 4, 1]
	theta = 1.2 

	print(np.dot(rotation_matrix(axis,theta), v)) 
	# [ 2.74911638  4.77180932  1.91629719]

    """
    axis = np.asarray(axis)
    theta = np.asarray(theta)
    axis = axis/np.sqrt(np.dot(axis, axis))
    a = np.cos(theta/2.0)
    b, c, d = -axis*np.sin(theta/2.0)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d
    return np.array([[aa+bb-cc-dd, 2*(bc+ad), 2*(bd-ac)],
                     [2*(bc-ad), aa+cc-bb-dd, 2*(cd+ab)],
                     [2*(bd+ac), 2*(cd-ab), aa+dd-bb-cc]])
    
    
def sphere(r=1.,n=100.):
    """
    Produce the polar coordinates of a sphere. 
    ______________________________________________________________________
    :type r, n: variables
    :param r, n: radius and number of resolution points.
    
    :rtype : list
    :return : 3d list of azimuth, polar angle and radial distance.

    .. seealso::

        numpy.linspace : produces the resolution vectors.

        numpy.meshgrid : produce the grid from the vectors.

    .. rubric:: Example

        # import the module
        import source

        # 100 coordinates on sphere or radius 5
        points = source.sphere(r=5, n=100)

        # Unit sphere of 50 points
        points = source.sphere(n=50)               

    .. plot::

        # run one of the example
        points = source.spherical_to_cartesian(points)

        # plot using matplotlib 
        import matplotlib.pyplot as plt
        fig = plt.figure()
        ax=fig.gca(projection='3d')
        ax.set_aspect("equal")
        ax.plot_wireframe(points[0], points[1], points[2], color="r")
        plt.show() 
    ______________________________________________________________________
    """
    # Get the resolution (sorry this is ugly)
    c = 0.038 ;
    na = n**(.5+c)
    nt = n**(.5-c)
    [a, t] = np.meshgrid( np.linspace(0, 2*np.pi, na+1), np.linspace(0, 1*np.pi, nt) )
    r = np.ones(a.shape)*r
    
    #golden_angle = np.pi * (3 - np.sqrt(5))
    #theta = golden_angle * np.arange(n)
    #z = np.linspace(1 - 1.0 / n, 1.0 / n - 1, n)
    #radius = np.sqrt(1 - z * z)
    
    #points = np.zeros((n, 3))
    #points[:,0] = radius * np.cos(theta)
    #points[:,1] = radius * np.sin(theta)
    #points[:,2] = z

    return [ a, t, r ] #cartesian_to_spherical(points.T) #


def cartesian_to_spherical(vector):
    """
    Convert the Cartesian vector [x, y, z] to spherical coordinates 
    [azimuth, polar angle, radial distance].
    ______________________________________________________________________
    :type vector : 3D array, list | np.array
    :param vector :  The vector of cartessian coordinates.

    :rtype : 3D array, np.array
    :return : The spherical coordinate vector.
    
    .. note::

        This file is extracted & modified from the program relax (Edward 
            d'Auvergne).

    .. seealso::
    
        http://svn.gna.org/svn/relax/1.3/maths_fns/coord_transform.py
    ______________________________________________________________________
    
    """

    # Make sure we got np.array 
    if np.asarray(vector) is not vector:
        vector = np.asarray(vector)

    # The radial distance.
    radius = np.sqrt((vector**2).sum(axis=0))

    # The horizontal radial distance.
    rh = np.sqrt(vector[0]**2 + vector[1]**2) 

    # The polar angle.
    takeoff = np.arccos( vector[2] / radius )
    takeoff[radius == 0.0] = np.pi / 2 * np.sign(vector[2][radius == 0.0])
    #theta = np.arctan2(vector[2], rh)

    # The azimuth.
    azimuth_trig = np.arctan2(vector[1], vector[0])

    # Return the spherical coordinate vector.
    return [azimuth_trig, takeoff, radius]


def spherical_to_cartesian(vector):
    """
    Convert the spherical coordinates [azimuth, polar angle
    radial distance] to Cartesian coordinates [x, y, z].

    ______________________________________________________________________
    :type vector : 3D array, list | np.array
    :param vector :  The spherical coordinate vector.

    :rtype : 3D array, np.array
    :return : The vector of cartesian coordinates.
    
    .. note::

        This file is extracted & modified from the program relax (Edward 
            d'Auvergne).

    .. seealso::
    
        http://svn.gna.org/svn/relax/1.3/maths_fns/coord_transform.py
    ______________________________________________________________________
    """

    # Unit vector if r is missing
    if len(vector) == 2 :
        radius =1
    else:
        radius=vector[2]

    # Trig alias.
    sin_takeoff = np.sin(vector[1])

    # The vector.
    x = radius * sin_takeoff * np.cos(vector[0])
    y = radius * sin_takeoff * np.sin(vector[0])
    z = radius * np.cos(vector[1])

    return [x, y, z]


def project_vectors(b, a):
    """
    Project the vectors b on vectors a.
    ______________________________________________________________________
    :type b : 3D np.array
    :param b :  The cartesian coordinates of vectors to be projected.

    :type a : 3D np.array
    :param a :  The cartesian coordinates of vectors to project onto.

    :rtype : 3D np.array
    :return : The cartesian coordinates of b projected on a.
    
    .. note::

        There is maybe better (built in numpy) ways to do this.

    .. seealso::
    
        :func:`numpy.dot()` 
        :func:`numpy.dotv()`
    ______________________________________________________________________
    """

    # Project 
    ## ratio (norm of b on a / norm of a)
    proj_norm = a[0]*b[0] + a[1]*b[1] + a[2]*b[2] 
    proj_norm /=  (a[0]**2 + a[1]**2 + a[2]**2)+0.0000000001
    ## project on a
    b_on_a = proj_norm * a


    return b_on_a


def vector_normal(XYZ, v_or_h):
    """
    Compute the vertical or horizontal normal vectors.
    ______________________________________________________________________
    :type XYZ : 3D np.array
    :param b :  The cartesian coordinates of vectors.

    :type v_or_h : string
    :param v_or_h :  The normal direction to pick.

    :rtype : 3D np.array
    :return : Requested normal on vertical or horizontal plane 
        ('v|vert|vertical' or 'h|horiz|horizontal').
    
    .. rubric:: _`Supported v_or_h`

        ``'v'``
            Vertical.

        ``'h'``
            horizontal.

        ``'r'``
            Radial component.

        ``'m'``
            The meridian component (to be prefered to vertical).

    .. note::

        There is maybe better (built in numpy) ways to do this.

    .. seealso::
    
        :func:`numpy.cross()` 
    ______________________________________________________________________
    """

    oneheightydeg =  np.ones(XYZ.shape) * np.pi
    ninetydeg =  np.ones(XYZ.shape) * np.pi/2.

    ATR = np.asarray(cartesian_to_spherical(XYZ))

    if v_or_h in ('m', 'meridian', 'n', 'nhr', 'normal horizontal radial', 'norm horiz rad'): 
        ATR_n = np.array([ ATR[0] , ATR[1] - ninetydeg[0], ATR[2]])
        XYZ_n = np.asarray(spherical_to_cartesian(ATR_n))
    elif v_or_h in ('h', 'horizontal', 'horiz'): 
        ATR_n = np.array([ ATR[0] - ninetydeg[0], ATR[1]+(ninetydeg[0]-ATR[1]) , ATR[2]])
        XYZ_n = np.asarray(spherical_to_cartesian(ATR_n))
    elif v_or_h in ('v', 'vertical', 'vertical'): 
        ATR_n = np.array([ ATR[0], ATR[1]-ATR[1] , ATR[2]])
        XYZ_n = np.asarray(spherical_to_cartesian(ATR_n))
    elif v_or_h in ('r', 'radial', 'self'): 
        XYZ_n = XYZ

    return XYZ_n

def mt_full(mt):
    """    
    Takes 6 components moment tensor and returns full 3x3 moment 
    tensor.
    ______________________________________________________________________
    :type mt : list or np.array.
    :param mt : moment tensor NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz, 
        the six independent components).

    :rtype : np.array 3x3.
    :return : full 3x3 moment tensor.

    .. note::

        Use obspy.imaging.scripts.mopad to get correct input.
    ______________________________________________________________________
    """

    # Make sure we got np.array 
    if np.asarray(mt) is not mt:
        mt = np.asarray(mt)

    if len(mt) == 6:        
        mt = np.array(([[mt[0], mt[3], mt[4]],
            [mt[3], mt[1], mt[5]],
            [mt[4], mt[5], mt[2]]]))

    if mt.shape != (3,3) :       
        raise Exception('I/O dimensions: only 1x6 or 3x3 input supported.')
    
    return mt


def mt_angles(mt): 
    """    
    Takes 6 components and returns fps tri-angles in degrees, with 
    deviatoric, isotropic, DC and CLVD percentages.
    ______________________________________________________________________
    :type mt : list or np.array.
    :param mt : moment tensor NM x 6 (Mxx, Myy, Mzz, 
        Mxy, Mxz, Myz, the six independent 
        components).

    :rtype : np.array [[1x3], [1x4]].
    :return : full 3x3 moment tensor.

    .. note::
        Nan value are returned for unknown parameters.

        The deviatoric percentage is the sum of DC and CLVD percentages.

        Use obspy.imaging.scripts.mopad to get correct input.
    ______________________________________________________________________
    """

    # Make sure we got np.array 
    if np.asarray(mt) is not mt:
        mt = np.asarray(mt)

    # Getting various formats
    ## if given strike, dip, rake
    if mt.shape == (3,):
        strike, dip, rake = mt
        DC = 100
        CLVD = 0
        iso = 0
        devi = 100
    
    ## if given [[strike, dip, rake], [strike, dip, rake]] (e.g. by MoPad)
    elif mt.shape == (2,3) :
        strike, dip, rake = mt[0]
        DC = 100
        CLVD = 0
        iso = 0
        devi = 100
    
    ## if given [strike, dip, rake, devi]
    elif mt.shape == (4,):
        strike, dip, rake, devi = mt
        DC = np.nan
        CLVD = np.nan
        iso = 0

    ## if given [Mxx, Myy, Mzz, Mxy, Mxz, Myz]
    elif mt.shape == (6,) :
        
        mt = MomentTensor(mt,'XYZ') 
        
        DC = mt.get_DC_percentage()
        CLVD = mt.get_CLVD_percentage()
        iso = mt.get_iso_percentage()
        devi = mt.get_devi_percentage()

        mt = mt_angles(mt.get_fps())
        strike, dip, rake = mt[0]

    ## if given full moment tensor
    elif mt.shape == (3,3) :

        mt = mt_angles([mt[0,0], mt[1,1], mt[2,2], mt[0,1], mt[0,2], mt[1,2]])

        strike, dip, rake = mt[0]
        DC, CLVD, iso, devi = mt[1]

    else:         
        raise Exception('I/O dimensions: only [1|2]x3, 1x[4|6] and 3x3 inputs supported.')

    return np.array([[strike, dip, rake], [DC, CLVD, iso, devi]])
    

def disp_component(xyz, disp,comp):
	
	## Get direction(s)
    if comp == None: 
        amplitude_direction = disp      
    else :
        amplitude_direction = vector_normal(xyz, comp)
    ## Project 
    disp_projected = project_vectors(disp, amplitude_direction) 
    ## Norms
    amplitudes = np.sqrt(disp_projected[0]**2 + disp_projected[1]**2 + disp_projected[2]**2) 
    ## Amplitudes (norm with sign)
    amplitudes *= np.sign(np.sum(disp * amplitude_direction, axis=0)+0.00001)
    
    return amplitudes, disp_projected 
    
    
def plot_seismicsourcemodel(disp, xyz, style='*', mt=None, comp=None, ax=None, alpha=0.5, wave='P', cbarxlabel=None) : 
    """
    Plot the given seismic wave radiation pattern as a color-coded surface 
    or focal sphere (not exactly as a beach ball diagram).
    ______________________________________________________________________
    :type G : 3D array, list | np.array
    :param G : The vector of cartessian coordinates of the radiation 
        pattern.

    :type xyz : 3D array, list | np.array
    :param xyz : The cartessian coordinates of the origin points of the
        radiation pattern.

    :type style : string
    :param style : type of plot.

    :type mt : list | np.array
    :param mt : moment tensor definition supported by MoPad, used in title.

    :type comp : string
    :param comp : component onto radiation pattern is projected to 
        infer amplitudes (norm and sign).

    :rtype : graphical object
    :return : The axe3d including plot.

    .. rubric:: _`Supported style`

        ``'*'``
            Plot options q, s and p together.

        ``'b'``
            Plot a unit sphere, amplitude sign being coded with color.
             (uses :func:`numpy.abs`).

        ``'q'``
            This a comet plot, displacements magnitudes, directions and 
             final state are given, respectively by the colors, lines and 
             points (as if looking at comets).  

        ``'s'``
            Plot the amplitudes as surface coding absolute amplitude as 
             radial distance from origin and amplitude polarity with color.
             (uses :func:`numpy.abs`).

        ``'f'``
            Plot the amplitudes as a wireframe, coding absolute amplitude as 
             radial distance. The displacement polarities are not 
             represented.

        ``'p'``
            Plot the polarities sectors using a colorcoded wireframe. 
             The magnitudes of displacements are not represented.

    .. rubric:: _`Supported comp`

        ``'None'``
            The radiation pattern is rendered as is if no comp option is 
            given (best for S wave).

        ``'v'``
            Vertical component (best for S or Sv wave).

        ``'h'``
            horizontal component (best for S or Sh waves, null for P).

        ``'r'``
            Radial component (best for P waves, null for S).

        ``'m'``
            The meridian component (best for S or Sn waves, null for P).

    .. note::

        The radiation pattern is rendered as is if no comp option is given.

        In the title of the plot, SDR stand for strike, dip, rake angles 
        and IDC stand for isotropic, double couple, compensated linear 
        vector dipole percentages.

    .. seealso::
    
        For earthquake focal mechanism rendering, use 
        obspy.imaging.beachball.Beachball() : 
        https://docs.obspy.org/packages/obspy.imaging.html#beachballs

        For more info see  and obspy.imaging.mopad_wrapper.Beachball().
    ______________________________________________________________________
    """

    # Component
    amplitudes, disp_projected = disp_component(xyz, disp, comp)
    
    ## Easiness
    U, V, W = disp_projected
    X, Y, Z = xyz
    amplitudes_surf = np.abs(amplitudes)/np.max(np.abs(amplitudes))

    # Initializing 
    ## Initializing the colormap machinery
    norm = matplotlib.colors.Normalize(vmin=np.min(amplitudes),vmax=np.max(amplitudes))
    c_m = matplotlib.cm.Spectral
    s_m = matplotlib.cm.ScalarMappable(cmap=c_m, norm=norm)
    s_m.set_array([])
    ## Initializing the plot
    if ax == None:
        fig = plt.figure(figsize=plt.figaspect(1.2))
        ax = fig.gca(projection='3d')  
    plt.xlabel('X')
    plt.ylabel('Y')
    ## Initializing the colorbar
    if style not in ('frame', 'wireframe') : 
        cbar = plt.colorbar(s_m,orientation="horizontal",fraction=0.07, ax = ax)
        if cbarxlabel==None:
        	cbarxlabel = 'Displacement amplitudes'
        cbar.ax.set_xlabel(cbarxlabel)
    ## Initializing figure keys
    if mt is not None :
        [strike, dip, rake], [DC, CLVD, iso, deviatoric] = mt_angles(mt)
        ax.set_title(r''+wave+'-wave\n(' + str(int(strike)) + ', ' + str(int(dip)) + ', ' + str(int(rake)) + ')$^{SDR}$, (' + str(int(iso)) + ', ' + str(int(DC)) + ', ' + str(int(CLVD)) + ')$^{\%IDC}$')
    
    ## Force axis equal
    arrow_scale = (np.max(xyz)-np.min(xyz))/10
    if style in ('p', 'polarities','b', 'bb', 'beachball'):
        max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max() / 2.0
    elif style in ('f', 'w', 'frame', 'wireframe', 's', 'surf', 'surface'): 
        max_range = np.array([(X*np.abs(amplitudes)).max()-(X*np.abs(amplitudes)).min(), (Y*np.abs(amplitudes)).max()-(Y*np.abs(amplitudes)).min(), (Z*np.abs(amplitudes)).max()-(Z*np.abs(amplitudes)).min()]).max() / 2.0
    else : 
        max_range = np.array([(X+arrow_scale).max()-(X+arrow_scale).min(), (Y+arrow_scale).max()-(Y+arrow_scale).min(), (Z+arrow_scale).max()-(Z+arrow_scale).min()]).max() / 2.0
    mean_x = X.mean()
    mean_y = Y.mean()
    mean_z = Z.mean()


    # Simple styles   
    ## For a wireframe surface representing amplitudes
    if style in ('f', 'w', 'frame', 'wireframe') :
        
        ax.plot_wireframe(X*amplitudes_surf, Y*amplitudes_surf, Z*amplitudes_surf, rstride=1, cstride=1, linewidth=0.5, alpha=alpha)

    ## For focal sphere, with amplitude sign (~not a beach ball diagram) on unit sphere 
    if style in ('*', 'p', 'polarities'):

        if style is '*':
            alpha =0.1

        polarity_area = amplitudes.copy()
        polarity_area[amplitudes > 0] = np.nan  
        polarity_area[amplitudes <= 0] = 1
        ax.plot_wireframe(X*polarity_area, Y*polarity_area, Z*polarity_area, color='r', rstride=1, cstride=1, linewidth=.5, alpha=alpha)

        polarity_area[amplitudes <= 0] = np.nan 
        polarity_area[amplitudes > 0] = 1
        ax.plot_wireframe(X*polarity_area, Y*polarity_area, Z*polarity_area, color='b', rstride=1, cstride=1, linewidth=.5, alpha=alpha)

    ## For ~ beach ball diagram 
    if style in ('b', 'bb', 'beachball'):

        polarity_area = amplitudes.copy()
        polarity_area[amplitudes >= 0] = 1  
        polarity_area[amplitudes < 0] = -1
        ax.plot_surface(X, Y, Z, linewidth=0, rstride=1, cstride=1, facecolors=s_m.to_rgba(polarity_area)) 

	## For focal sphere, with amplitude colorcoded on unit sphere
    if style in ('x'):

        ax.plot_surface(X, Y, Z, linewidth=0, rstride=1, cstride=1, facecolors=s_m.to_rgba(amplitudes), alpha=alpha) 
	       
    # Complexe styles
    ## For arrow vectors on obs points
    if style in ('*', 'q', 'a', 'v', 'quiver', 'arrow', 'vect', 'vector', 'vectors') :    

        cmap = plt.get_cmap()
        # qs = ax.quiver(X.flatten(), Y.flatten(), Z.flatten(), U.flatten(), V.flatten(), W.flatten(), pivot='tail', length=arrow_scale ) 
        # qs.set_color(s_m.to_rgba(amplitudes.flatten())) #set_array(np.transpose(amplitudes.flatten()))

        Us, Vs, Ws = disp_projected * arrow_scale / disp_projected.max()
        ax.scatter((X+Us).flatten(), (Y+Vs).flatten(), (Z+Ws).flatten(), c=s_m.to_rgba(amplitudes.flatten()), marker='.', linewidths=0)

        for i, x_val in np.ndenumerate(X):
            ax.plot([X[i], X[i]+Us[i]], [Y[i], Y[i]+Vs[i]], [Z[i], Z[i]+Ws[i]],'-', color=s_m.to_rgba(amplitudes[i]) , linewidth=1)
        

    ## For a color-coded surface representing amplitudes
    if style in ('*', 's', 'surf', 'surface'):

        ax.plot_surface(X*amplitudes_surf, Y*amplitudes_surf, Z*amplitudes_surf,linewidth=0.5, rstride=1, cstride=1, facecolors=s_m.to_rgba(amplitudes))    

    
	
    ax.set_xlim(mean_x - max_range, mean_x + max_range)
    ax.set_ylim(mean_y - max_range, mean_y + max_range)
    ax.set_zlim(mean_z - max_range, mean_z + max_range)
    plt.show() 
    return ax


def energy_seismicsourcemodel(G, XYZ) :    
    """
    Evaluate statistical properties of the given seismic wave radiation 
    pattern.
    ______________________________________________________________________
    :type G : 3D array, list | np.array
    :param G : The vector of cartessian coordinates of the radiation 
        pattern.

    :type XYZ : 3D array, list | np.array
    :param XYZ : The cartessian coordinates of the origin points of the
        radiation pattern.

    :rtype : list
    :return : The statistical properties of amplitudes [rms, euclidian norm, average].

    .. todo::

        Compute more properties, add request handling.
    ______________________________________________________________________
    """

    #amplitudes_correction = np.sum(G * XYZ, axis=0)
    #amplitudes_correction /= np.max(np.abs(amplitudes_correction))
    amplitudes = np.sqrt( G[0]**2 + G[1]**2 + G[2]**2 ) #* amplitudes_correction            
    
    weigths = (np.max(abs(amplitudes))- amplitudes)**2
    
    # Classic rms
    rms = np.sqrt(np.nansum((weigths*amplitudes)**2)/np.sum(weigths)) # prod(amplitudes.shape))
    # Euclidian norm
    norm = np.sqrt(np.nansum((weigths*amplitudes)**2))
    # Amplitude average
    average = np.nansum(np.abs(amplitudes*weigths))/np.sum(weigths)
    
    return [rms, norm, average]


class Aki_Richards(object):
    """
    Set an instance of class Aki_Richards() that can be used for 
    earthquake modeling based on Aki and Richards (2002, eq. 4.29).
    ______________________________________________________________________
    :type mt : list
    :param mt : The focal mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - 
        the six independent components of the moment tensor).

    .. note::

        This object is composed of three methods : radpat, plot and 
        energy.

    .. seealso::

            :meth: `radpat`
            :meth: `plot`
            :meth: `energy`            
    ______________________________________________________________________

    """  

    def __init__(self, mt):
        self.mt = mt
        
    def radpat(self, wave='P', obs_cart='None', obs_sph='None'):
        """
        Returns the farfield radiation pattern (normalized displacement) based 
        on Aki and Richards (2002, eq. 4.29) and the cartesian coordinates of 
        the observation points.
        ______________________________________________________________________
        :type self : object: Aki_Richards
        :param self : This method use de self.mt attribute, i.e. the focal 
            mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - the six 
            independent components of the moment tensor)

        :type wave: String
        :param wave: type of wave to compute

        :type obs_cart : list | np.array 
        :param obs_cart : 3D vector array specifying the observations points
            in cartesian coordinates. 

        :type obs_sph : list | np.array 
        :param obs_sph : 3D vector array specifying the observations points
            in spherical coordinates (radians). The default is a unit sphere.

        :rtype : np.array 
        :return : 3D vector array with same shape than requested, that 
            contains the displacement vector for each observation point.

        .. rubric:: _`Supported wave`

            ``'P'``
                Bodywave P.

            ``'S' or 'S wave' or 'S-wave``
                Bodywave S.

            ``'Sv'``
                Projection of S on the vertical.

            ``'Sh'``
                Projection of S on the parallels of the focal sphere. 

            ``'Sm'``
                Projection of S on the meridian of the focal sphere.

        .. note::

            This is based on MMesch, ObsPy, radpattern.py :
                https://github.com/MMesch/obspy/blob/radpattern/obspy/core/event/radpattern.py

        .. seealso::
    
            Aki, K., & Richards, P. G. (2002). Quantitative Seismology. (J. 
                Ellis, Ed.) (2nd ed.). University Science Books

        .. todo::

            Implement Sv and Sh wave (see below)
        ______________________________________________________________________
        """

        # Special cases ######################################################
        if wave in ('Sv', 'Sv', 'S_v', 'Sv wave', 'Sv-wave'):

            ## Get S waves
            disp, obs_cart = self.radpat(wave='S', obs_cart=obs_cart, obs_sph=obs_sph)
            ## Project on Sv component
            disp = project_vectors(disp, vector_normal(obs_cart, 'v')) 

            return disp, obs_cart

        elif wave in ('Sm', 'SM', 'SN', 'Sn', 'Snrh', 'Snrh wave', 'Snrh-wave'):

            ## Get S waves
            disp, obs_cart = self.radpat(wave='S', obs_cart=obs_cart, obs_sph=obs_sph)
            ## Project on Sh component
            disp = project_vectors(disp, vector_normal(obs_cart, 'm')) 

            return disp, obs_cart

        elif wave in ('SH', 'Sh', 'S_h', 'Sh wave', 'Sh-wave'):

            ## Get S waves
            disp, obs_cart = self.radpat(wave='S', obs_cart=obs_cart, obs_sph=obs_sph)
            ## Project on Sh component
            disp = project_vectors(disp, vector_normal(obs_cart, 'h')) 

            return disp, obs_cart
        ######################################################################

        # Get full mt
        Mpq = mt_full(self.mt)
        

        # Get observation points
        if obs_sph == 'None':
            obs_sph = sphere(r=1.,n=1000.)
        ## Get unit sphere, or spherical coordinate if given 
        if obs_cart == 'None' :
            obs_cart = spherical_to_cartesian(obs_sph)
        ## Make sure they are np.array 
        if np.asarray(obs_cart) is not obs_cart:
            obs_cart = np.asarray(obs_cart)
        ## Keeping that in mind
        requestdimension = obs_cart.shape
        obs_cart = np.reshape(obs_cart, (3, np.prod(requestdimension)/3))
        
        # Displacement array    
        # precompute directional cosine array
        dists = np.sqrt(obs_cart[0] * obs_cart[0] + obs_cart[1] * obs_cart[1] +
                        obs_cart[2] * obs_cart[2])

        # In gamma, all points are taken to a unit distance, same angle:
        gammas = obs_cart / dists

        # initialize displacement array
        ndim, npoints = obs_cart.shape
        disp = np.empty(obs_cart.shape)

        # loop through points
        for ipoint in range(npoints):
            
            gamma = gammas[:, ipoint]

            if wave in ('S', 'S wave', 'S-wave'):

                # loop through displacement component [n index]
                Mp = np.dot(Mpq, gamma)
                for n in range(ndim):
                    psum = 0.0
                    for p in range(ndim):
                        deltanp = int(n == p)
                        psum += (gamma[n] * gamma[p] - deltanp) * Mp[p]
                    disp[n, ipoint] = psum

            elif wave in ('P', 'P wave', 'P-wave'):

                gammapq = np.outer(gamma, gamma)
                gammatimesmt = gammapq * Mpq
                
                # loop through displacement component [n index]
                for n in range(ndim):
                    disp[n, ipoint] = gamma[n] * np.sum(gammatimesmt.flatten())

        # Reshape to request dimensions
        obs_cart = np.reshape(obs_cart, requestdimension)
        disp = np.reshape(disp, requestdimension)

        return disp, obs_cart

    def plot(self, wave='P',style='*', comp=None, ax=None, cbarxlabel=None) :
        """
        Plot the radiation pattern.
        ______________________________________________________________________
        :type self : object: Aki_Richards
        :param self : This method use de self.mt attribute, i.e. the focal 
            mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - the six 
            independent components of the moment tensor)

        :type wave: String
        :param wave: type of wave to compute

        :type style : string
        :param style : type of plot.

        :type comp : string
        :param comp : component onto radiation pattern is projected to 
            infer amplitudes (norm and sign).

        :rtype : graphical object
        :return : The axe3d including plot.

        .. rubric:: _`Supported wave`

            ``'P'``
                Bodywave P.

            ``'S' or 'S wave' or 'S-wave``
                Bodywave S.

            ``'Sv'``
                Projection of S on the vertical.

            ``'Sh'``
                Projection of S on the parallels of the focal sphere. 

            ``'Sm'``
                Projection of S on the meridian of the focal sphere.

        .. rubric:: _`Supported style`

            ``'*'``
                Plot options q, s and p together.

            ``'b'``
                Plot a unit sphere, amplitude sign being coded with color.
                 (uses :func:`numpy.abs`).

            ``'q'``
                This a comet plot, displacements magnitudes, directions and 
                 final state are given, respectively by the colors, lines and 
                 points (as if looking at comets).  

            ``'s'``
                Plot the amplitudes as surface coding absolute amplitude as 
                 radial distance from origin and amplitude polarity with color.
                 (uses :func:`numpy.abs`).

            ``'f'``
                Plot the amplitudes as a wireframe, coding absolute amplitude as 
                 radial distance. The displacement polarities are not 
                 represented.

            ``'p'``
                Plot the polarities sectors using a colorcoded wireframe. 
                 The magnitudes of displacements are not represented.

        .. rubric:: _`Supported comp`

            ``'None'``
                The radiation pattern is rendered as is if no comp option is 
                given (best for S wave).

            ``'v'``
                Vertical component (best for S or Sv wave).

            ``'h'``
                horizontal component (best for S or Sh waves, null for P).

            ``'r'``
                Radial component (best for P waves, null for S).

            ``'n'``
                The meridian component (best for S or Sn waves, null for P).

        .. note::

            The radiation pattern is rendered as is if no comp option is given.

            In the title of the plot, SDR stand for strike, dip, rake angles 
            and IDC stand for isotropic, double couple, compensated linear 
            vector dipole percentages.

        .. seealso::

                :func: `plot_seismicsourcemodel`
                :class: `Aki_Richards.radpat`
        ______________________________________________________________________

        """
        # Get radiation pattern
        G, XYZ = self.radpat(wave)
        if comp == None :
            if wave in ('Sv', 'Sv wave', 'Sv-wave'):
                comp='v'
            elif wave in ('Sm', 'Sn', 'Snrh','Snrh wave', 'Snrh-wave'):
                comp='m'
            elif wave in ('Sh', 'Sh wave', 'Sh-wave'):
                comp='h'
            elif wave in ('P', 'P wave', 'P-wave'):
                comp='r'

        plot_seismicsourcemodel(G, XYZ, style=style, mt=self.mt, comp=comp, ax=ax, wave=wave, cbarxlabel=cbarxlabel)

    def energy(self, wave='P') :   
        """
        Get statistical properties of radiation pattern.
        ______________________________________________________________________
        :type self : object: Aki_Richards
        :param self : This method use de self.mt attribute, i.e. the focal 
            mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - the six 
            independent components of the moment tensor)

        :type wave: string
        :param wave: type of wave to compute

        :rtype : list
        :return : The statistical properties of amplitudes [rms, euclidian norm, average].

        .. rubric:: _`Supported wave`

            ``'P'``
                Bodywave P.

            ``'S' or 'S wave' or 'S-wave``
                Bodywave S.

            ``'Sv'``
                Projection of S on the vertical.

            ``'Sh'``
                Projection of S on the parallels of the focal sphere. 

            ``'Sm'``
                Projection of S on the meridian of the focal sphere.

        .. seealso::

                :func: `energy_seismicsourcemodel`
                :class: `Aki_Richards.radpat`
        ______________________________________________________________________

        """ 

        # Get radiation pattern and estimate energy
        G, XYZ = self.radpat(wave)  
        estimators = energy_seismicsourcemodel(G, XYZ)
        return estimators


class Vavryeuk(object):
    """
    Set an instance of class Vavryeuk() that can be used for 
    earthquake modeling based on Vavryèuk (2001).
    ______________________________________________________________________
    :type mt : list
    :param mt : The focal mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - 
        the six independent components of the moment tensor).

    :type poisson: variable
    :param poisson: Poisson coefficient (0.25 by default).

    .. note::

        This object is composed of three methods : radpat, plot and 
        energy.

    .. seealso::

            :meth: `radpat`
            :meth: `plot`
            :meth: `energy`            
    ______________________________________________________________________

    """  

    def __init__(self, mt, poisson=0.25):
        self.mt = mt
        self.poisson = poisson
        
    def radpat(self, wave='P', obs_cart='None', obs_sph='None'):
        """
        Returns the farfield radiation pattern (normalized displacement) based 
        on Vavryèuk (2001) and the cartesian coordinates of the observation 
        points.
        ______________________________________________________________________
        :type self : object: Vavryeuk
        :param self : This method use de self.poisson and self.mt attributes, 
            i.e. the focal mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - 
            the six independent components of the moment tensor).

        :type wave: String
        :param wave: type of wave to compute

        :type obs_cart : list | np.array 
        :param obs_cart : 3D vector array specifying the observations points
            in cartesian coordinates. 

        :type obs_sph : list | np.array 
        :param obs_sph : 3D vector array specifying the observations points
            in spherical coordinates (radians). The default is a unit sphere. 

        :rtype : np.array 
        :return : 3D vector array with same shape than requested, that 
            contains the displacement vector for each observation point.

        .. rubric:: _`Supported wave`

            ``'P'``
                Bodywave P.

            ``'S' or 'S wave' or 'S-wave``
                Bodywave S.

            ``'Sv'``
                Projection of S on the vertical.

            ``'Sh'``
                Projection of S on the parallels of the focal sphere. 

        .. note::

            This is based on Kwiatek, G. (2013/09/15). Radiation pattern from 
            shear-tensile seismic source. Revision: 1.3 :
            http://www.npworks.com/matlabcentral/fileexchange/43524-radiation-pattern-from-shear-tensile-seismic-source

        .. seealso::            

            [1] Vavryèuk, V., 2001. Inversion for parameters of tensile 
             earthquakes.” J. Geophys. Res. 106 (B8): 16339–16355. 
             doi: 10.1029/2001JB000372.

            [2] Ou, G.-B., 2008, Seismological Studies for Tensile Faults. 
             Terrestrial, Atmospheric and Oceanic Sciences 19, 463.

            [3] Kwiatek, G. and Y. Ben-Zion (2013). Assessment of P and S wave 
             energy radiated from very small shear-tensile seismic events in 
             a deep South African mine. J. Geophys. Res. 118, 3630-3641, 
             doi: 10.1002/jgrb.50274

        .. rubric:: Example

            ex = NnK.source.SeismicSource([0,0,0,0,0,1])
            Svect, obs =  ex.Vavryeuk.radpat('S')                   

        .. plot::

            ex.Vavryeuk.plot()
        ______________________________________________________________________

        """
        # 1) Calculate moving rms and average, see moving()
        # 2) ...
        # 3) ... 
        
        poisson = self.poisson

        # Get angle from moment tensor
        [strike, dip, rake], [DC, CLVD, iso, deviatoric] = mt_angles(self.mt) 
        ## in radians
        [strike, dip, rake] = np.deg2rad([strike, dip, rake])
        ## convert DC ratio to angle
        MODE1 = np.arcsin((100-DC)/100.)        

        # Get observation points
        if obs_cart == 'None' :
            obs_cart = spherical_to_cartesian(sphere(r=1.,n=1000.))
        ## Get unit sphere, or spherical coordinate if given 
        if obs_sph == 'None' :
            obs_sph = cartesian_to_spherical(obs_cart)
        else:
            obs_cart = spherical_to_cartesian(obs_sph)

        ## Make sure they are np.array 
        if np.asarray(obs_sph) is not obs_sph:
            obs_sph = np.asarray(obs_sph)
        if np.asarray(obs_cart) is not obs_cart:
            obs_cart = np.asarray(obs_cart)
        
        # Radiation patterns
        # G is the amplitude for each observation point
        ## Observations are given in spherical angles
        AZM = obs_sph[0]
        TKO = obs_sph[1]

        ## Make sure we got np.array 
        if np.asarray(TKO) is not TKO:
            TKO = np.asarray(TKO)
        if np.asarray(AZM) is not AZM:
            AZM = np.asarray(AZM)

        ## Tensile definitions by Vavryèuk (2001)
        if wave in ('P', 'P-wave', 'P wave'):
            G = np.cos(TKO)*(np.cos(TKO)*(np.sin(MODE1)*(2*np.cos(dip)**2 - (2*poisson)/(2*poisson - 1)) + np.sin(2*dip)*np.cos(MODE1)*np.sin(rake)) - np.cos(AZM)*np.sin(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.sin(rake)*np.sin(strike) + np.cos(dip)*np.cos(rake)*np.cos(strike)) - np.sin(2*dip)*np.sin(MODE1)*np.sin(strike)) + np.sin(AZM)*np.sin(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.cos(strike)*np.sin(rake) - np.cos(dip)*np.cos(rake)*np.sin(strike)) - np.sin(2*dip)*np.cos(strike)*np.sin(MODE1))) + np.sin(AZM)*np.sin(TKO)*(np.cos(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.cos(strike)*np.sin(rake) - np.cos(dip)*np.cos(rake)*np.sin(strike)) - np.sin(2*dip)*np.cos(strike)*np.sin(MODE1)) + np.cos(AZM)*np.sin(TKO)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)) + np.sin(AZM)*np.sin(TKO)*(np.cos(MODE1)*(np.sin(2*strike)*np.cos(rake)*np.sin(dip) - np.sin(2*dip)*np.cos(strike)**2*np.sin(rake)) - np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.cos(strike)**2*np.sin(dip)**2))) - np.cos(AZM)*np.sin(TKO)*(np.cos(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.sin(rake)*np.sin(strike) + np.cos(dip)*np.cos(rake)*np.cos(strike)) - np.sin(2*dip)*np.sin(MODE1)*np.sin(strike)) - np.sin(AZM)*np.sin(TKO)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)) + np.cos(AZM)*np.sin(TKO)*(np.cos(MODE1)*(np.sin(2*dip)*np.sin(rake)*np.sin(strike)**2 + np.sin(2*strike)*np.cos(rake)*np.sin(dip)) + np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.sin(dip)**2*np.sin(strike)**2)))
        
        elif wave in ('SH', 'Sh', 'Sh-wave', 'Sh wave', 'SH-wave', 'SH wave'):
            G = np.cos(TKO)*(np.cos(AZM)*(np.cos(MODE1)*(np.cos(2*dip)*np.cos(strike)*np.sin(rake) - np.cos(dip)*np.cos(rake)*np.sin(strike)) - np.sin(2*dip)*np.cos(strike)*np.sin(MODE1)) + np.sin(AZM)*(np.cos(MODE1)*(np.cos(2*dip)*np.sin(rake)*np.sin(strike) + np.cos(dip)*np.cos(rake)*np.cos(strike)) - np.sin(2*dip)*np.sin(MODE1)*np.sin(strike))) - np.sin(AZM)*np.sin(TKO)*(np.sin(AZM)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)) - np.cos(AZM)*(np.cos(MODE1)*(np.sin(2*strike)*np.cos(rake)*np.sin(dip) - np.sin(2*dip)*np.cos(strike)**2*np.sin(rake)) - np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.cos(strike)**2*np.sin(dip)**2))) + np.cos(AZM)*np.sin(TKO)*(np.sin(AZM)*(np.cos(MODE1)*(np.sin(2*dip)*np.sin(rake)*np.sin(strike)**2 + np.sin(2*strike)*np.cos(rake)*np.sin(dip)) + np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.sin(dip)**2*np.sin(strike)**2)) + np.cos(AZM)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)))
            
        elif wave in ('SV', 'Sv', 'Sv-wave', 'Sv wave', 'SV-wave', 'SV wave'):
            G = np.sin(AZM)*np.sin(TKO)*(np.cos(AZM)*np.cos(TKO)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)) - np.sin(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.cos(strike)*np.sin(rake) - np.cos(dip)*np.cos(rake)*np.sin(strike)) - np.sin(2*dip)*np.cos(strike)*np.sin(MODE1)) + np.cos(TKO)*np.sin(AZM)*(np.cos(MODE1)*(np.sin(2*strike)*np.cos(rake)*np.sin(dip) - np.sin(2*dip)*np.cos(strike)**2*np.sin(rake)) - np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.cos(strike)**2*np.sin(dip)**2))) - np.cos(TKO)*(np.sin(TKO)*(np.sin(MODE1)*(2*np.cos(dip)**2 - (2*poisson)/(2*poisson - 1)) + np.sin(2*dip)*np.cos(MODE1)*np.sin(rake)) + np.cos(AZM)*np.cos(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.sin(rake)*np.sin(strike) + np.cos(dip)*np.cos(rake)*np.cos(strike)) - np.sin(2*dip)*np.sin(MODE1)*np.sin(strike)) - np.cos(TKO)*np.sin(AZM)*(np.cos(MODE1)*(np.cos(2*dip)*np.cos(strike)*np.sin(rake) - np.cos(dip)*np.cos(rake)*np.sin(strike)) - np.sin(2*dip)*np.cos(strike)*np.sin(MODE1))) + np.cos(AZM)*np.sin(TKO)*(np.sin(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.sin(rake)*np.sin(strike) + np.cos(dip)*np.cos(rake)*np.cos(strike)) - np.sin(2*dip)*np.sin(MODE1)*np.sin(strike)) + np.cos(TKO)*np.sin(AZM)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)) - np.cos(AZM)*np.cos(TKO)*(np.cos(MODE1)*(np.sin(2*dip)*np.sin(rake)*np.sin(strike)**2 + np.sin(2*strike)*np.cos(rake)*np.sin(dip)) + np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.sin(dip)**2*np.sin(strike)**2)))
        
        ## Re-using the same programme to get other things ... 
        elif wave in ('S', 'S-wave', 'S wave'):

            # for such definition this the less ugly
            Gsh = np.cos(TKO)*(np.cos(AZM)*(np.cos(MODE1)*(np.cos(2*dip)*np.cos(strike)*np.sin(rake) - np.cos(dip)*np.cos(rake)*np.sin(strike)) - np.sin(2*dip)*np.cos(strike)*np.sin(MODE1)) + np.sin(AZM)*(np.cos(MODE1)*(np.cos(2*dip)*np.sin(rake)*np.sin(strike) + np.cos(dip)*np.cos(rake)*np.cos(strike)) - np.sin(2*dip)*np.sin(MODE1)*np.sin(strike))) - np.sin(AZM)*np.sin(TKO)*(np.sin(AZM)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)) - np.cos(AZM)*(np.cos(MODE1)*(np.sin(2*strike)*np.cos(rake)*np.sin(dip) - np.sin(2*dip)*np.cos(strike)**2*np.sin(rake)) - np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.cos(strike)**2*np.sin(dip)**2))) + np.cos(AZM)*np.sin(TKO)*(np.sin(AZM)*(np.cos(MODE1)*(np.sin(2*dip)*np.sin(rake)*np.sin(strike)**2 + np.sin(2*strike)*np.cos(rake)*np.sin(dip)) + np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.sin(dip)**2*np.sin(strike)**2)) + np.cos(AZM)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)))
            Gsv = np.sin(AZM)*np.sin(TKO)*(np.cos(AZM)*np.cos(TKO)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)) - np.sin(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.cos(strike)*np.sin(rake) - np.cos(dip)*np.cos(rake)*np.sin(strike)) - np.sin(2*dip)*np.cos(strike)*np.sin(MODE1)) + np.cos(TKO)*np.sin(AZM)*(np.cos(MODE1)*(np.sin(2*strike)*np.cos(rake)*np.sin(dip) - np.sin(2*dip)*np.cos(strike)**2*np.sin(rake)) - np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.cos(strike)**2*np.sin(dip)**2))) - np.cos(TKO)*(np.sin(TKO)*(np.sin(MODE1)*(2*np.cos(dip)**2 - (2*poisson)/(2*poisson - 1)) + np.sin(2*dip)*np.cos(MODE1)*np.sin(rake)) + np.cos(AZM)*np.cos(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.sin(rake)*np.sin(strike) + np.cos(dip)*np.cos(rake)*np.cos(strike)) - np.sin(2*dip)*np.sin(MODE1)*np.sin(strike)) - np.cos(TKO)*np.sin(AZM)*(np.cos(MODE1)*(np.cos(2*dip)*np.cos(strike)*np.sin(rake) - np.cos(dip)*np.cos(rake)*np.sin(strike)) - np.sin(2*dip)*np.cos(strike)*np.sin(MODE1))) + np.cos(AZM)*np.sin(TKO)*(np.sin(TKO)*(np.cos(MODE1)*(np.cos(2*dip)*np.sin(rake)*np.sin(strike) + np.cos(dip)*np.cos(rake)*np.cos(strike)) - np.sin(2*dip)*np.sin(MODE1)*np.sin(strike)) + np.cos(TKO)*np.sin(AZM)*(np.cos(MODE1)*(np.cos(2*strike)*np.cos(rake)*np.sin(dip) + (np.sin(2*dip)*np.sin(2*strike)*np.sin(rake))/2) - np.sin(2*strike)*np.sin(dip)**2*np.sin(MODE1)) - np.cos(AZM)*np.cos(TKO)*(np.cos(MODE1)*(np.sin(2*dip)*np.sin(rake)*np.sin(strike)**2 + np.sin(2*strike)*np.cos(rake)*np.sin(dip)) + np.sin(MODE1)*((2*poisson)/(2*poisson - 1) - 2*np.sin(dip)**2*np.sin(strike)**2)))

            G = np.sqrt(Gsh**2 + Gsv**2)

        elif wave in ('S/P', 's/p'):
            G = self.radpat('S', )/self.radpat('P', obs_sph = obs_sph)  

        elif wave in ('P/S', 'p/s'):
            G, poubelle  = self.radpat('P', obs_sph = obs_sph)/self.radpat('S', obs_sph = obs_sph)  

        elif wave in ('SH/P', 'sh/p'):
            G, poubelle  = self.radpat('SH', obs_sph = obs_sph)/self.radpat('P', obs_sph = obs_sph)

        elif wave in ('SV/P', 'sv/p'):
            G, poubelle  = self.radpat('SV', obs_sph = obs_sph)/self.radpat('P', obs_sph = obs_sph)

        elif wave in ('SH/S', 'sh/s'):
            G, poubelle  = self.radpat('SH', obs_sph = obs_sph)/self.radpat('S', obs_sph = obs_sph)

        elif wave in ('SV/S', 'sv/s'):
            G, poubelle  = self.radpat('SV', obs_sph = obs_sph)/self.radpat('S', obs_sph = obs_sph)

        ## Making sure you get that error.
        else:
            print 'Can t yet compute this wave type.'

        ## transform G into vector x,y,z          
        G_cart = spherical_to_cartesian(np.asarray([AZM, TKO, G]))
        obs_cart = spherical_to_cartesian(np.asarray([AZM, TKO]))

        #return G, [AZM, TKO] 
        return np.asarray(G_cart), np.asarray(obs_cart)


    def plot(self, wave='P',style='*', ax=None, cbarxlabel=None) :
        """
        Plot the radiation pattern.
        ______________________________________________________________________
        :type self : object: Vavryeuk
        :param self : This method use de self.mt attribute, i.e. the focal 
            mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - the six 
            independent components of the moment tensor)

        :type wave: String
        :param wave: type of wave to compute

        :type style : string
        :param style : type of plot.

        :rtype : graphical object
        :return : The axe3d including plot.

        .. rubric:: _`Supported wave`

            ``'P'``
                Bodywave P.

            ``'S' or 'S wave' or 'S-wave``
                Bodywave S.

            ``'Sv'``
                Projection of S on the vertical.

            ``'Sh'``
                Projection of S on the parallels of the focal sphere. 

        .. rubric:: _`Supported style`

            ``'*'``
                Plot options q, s and p together.

            ``'b'``
                Plot a unit sphere, amplitude sign being coded with color.
                 (uses :func:`numpy.abs`).

            ``'q'``
                This a comet plot, displacements magnitudes, directions and 
                 final state are given, respectively by the colors, lines and 
                 points (as if looking at comets).  

            ``'s'``
                Plot the amplitudes as surface coding absolute amplitude as 
                 radial distance from origin and amplitude polarity with color.
                 (uses :func:`numpy.abs`).

            ``'f'``
                Plot the amplitudes as a wireframe, coding absolute amplitude as 
                 radial distance. The displacement polarities are not 
                 represented.

            ``'p'``
                Plot the polarities sectors using a colorcoded wireframe. 
                 The magnitudes of displacements are not represented.

        .. note::

            The radiation pattern is rendered as is if no comp option is given.

            In the title of the plot, SDR stand for strike, dip, rake angles 
            and IDC stand for isotropic, double couple, compensated linear 
            vector dipole percentages.

        .. seealso::

                :func: `plot_seismicsourcemodel`
                :class: `Vavryeuk.radpat`
        ______________________________________________________________________

        """

        # Get radiation pattern and plot
        G, XYZ = self.radpat(wave)
        plot_seismicsourcemodel(G, XYZ, style=style, mt=self.mt, comp='r',ax=ax, cbarxlabel=cbarxlabel)

    def energy(self, wave='P') :   
        """
        Get statistical properties of radiation pattern.
        ______________________________________________________________________
        :type self : object: Vavryeuk
        :param self : This method use de self.mt attribute, i.e. the focal 
            mechanism NM x 6 (Mxx, Myy, Mzz, Mxy, Mxz, Myz - the six 
            independent components of the moment tensor)

        :type wave: string
        :param wave: type of wave to compute

        :rtype : list
        :return : The statistical properties of amplitudes [rms, euclidian norm, average].

        .. rubric:: _`Supported wave`

            ``'P'``
                Bodywave P.

            ``'S' or 'S wave' or 'S-wave``
                Bodywave S.

            ``'Sv'``
                Projection of S on the vertical.

            ``'Sh'``
                Projection of S on the parallels of the focal sphere. 

        .. seealso::

                :func: `energy_seismicsourcemodel`
                :class: `Vavryeuk.radpat`
        ______________________________________________________________________

        """  
        # Get radiation pattern and estimate energy
        G, XYZ = self.radpat(wave)  
        estimators = energy_seismicsourcemodel(G, XYZ)
        return estimators



class SeismicSource(object):
    """
    Set an instance of class SeismicSource() that can be used for 
    earthquake modeling.
    ______________________________________________________________________
    :type mt : list
    :param mt : Definition of the focal mechanism supported 
        obspy.imaging.scripts.mopad.MomentTensor().

    :type poisson: variable
    :param poisson: Poisson coefficient (0.25 by default).

    .. example::

        ex = NnK.source.SeismicSource([1,2,3,4,5,6])
        ex.Aki_Richards.plot('P')

    .. note::

        This object is composed of three classes : MomentTensor, 
        Aki_Richards and Vavryeuk.

    .. seealso::

            :class: `obspy.imaging.scripts.mopad.MomentTensor`
            :class: `Aki_Richards`
            :class: `Vavryeuk`            
    ______________________________________________________________________

    """  
    # General attribut definition
    notes = 'Ceci est à moi'

    def __init__(self, mt, poisson=0.25):
		self.MomentTensor = MomentTensor(mt,debug=2)
		self.Aki_Richards = Aki_Richards(np.asarray(self.MomentTensor.get_M('XYZ')))  
		self.Vavryeuk     = Vavryeuk(np.asarray(self.MomentTensor.get_M('XYZ')),poisson = poisson)  


def degrade(wavelets, shift = [-.1, .1], snr = [.5, 5.]):
    
    shift = np.random.random_integers(int(shift[0]*1000), int(shift[1]*1000), wavelets.shape[0])/1000. # np.linspace(shift[0], shift[1], wavelets.shape[0])
    snr = np.random.random_integers(int(snr[0]*1000), int(snr[1]*1000), wavelets.shape[0])/1000. # np.linspace(snr[0], snr[1], wavelets.shape[0])

    for i,w in enumerate(wavelets):
        
        tmp = np.max(abs(wavelets[i])).copy()
        wavelets[i] += (np.random.random_integers(-100,100,wavelets.shape[1])/100.) * np.max(wavelets[i])/snr[i]
        wavelets[i] /= tmp #*np.max(abs(self.wavelets[i]))
        
        tmp = np.zeros( len(wavelets[i])*3. )
        index = [ int(len(wavelets[i])+(shift[i]*len(wavelets[i]))), 0 ]
        index[1] = index[0]+len(wavelets[i])
        tmp[index[0]:index[1]] = wavelets[i, :int(np.diff(index)) ]
        wavelets[i,-len(wavelets[i]):] = tmp[-2*len(wavelets[i]):-len(wavelets[i])]
    
    return wavelets

def plot_wavelet(data, style = '*'):
    
    fig = plt.figure(figsize=plt.figaspect(.5))
    ax1 = fig.add_subplot(1, 2, 1, projection='3d', aspect='equal', ylim=[-1,1], xlim=[-1,1], zlim=[-1,1])
    data.source.Aki_Richards.plot(wave='P', style='s', ax=ax1)
    ax1.scatter(data.obs_cart[0][data.wavelets[:,1]>=0],data.obs_cart[1][data.wavelets[:,1]>=0],data.obs_cart[2][data.wavelets[:,1]>=0],c='b')
    ax1.scatter(data.obs_cart[0][data.wavelets[:,1]<0],data.obs_cart[1][data.wavelets[:,1]<0],data.obs_cart[2][data.wavelets[:,1]<0],c='r')
    for i in range(data.n_wavelet):
        ax1.text(data.obs_cart[0][i],data.obs_cart[1][i],data.obs_cart[2][i],  '%s' % (str(i)))
    ax2 = fig.add_subplot(1, 2, 2, xlim=[0,data.wavelets.shape[1]-1]) #, ylim=[-1,(self.n_wavelet)/100.+1.]
    ax2.plot(np.transpose(data.wavelets))# + np.tile(range(self.n_wavelet), (self.wavelets.shape[1], 1))/100.);


class ArticialWavelets(object):
    """
        Set an instance of class ArticialWavelets() that can be used to get
        artificial wavelets.
        ______________________________________________________________________
        
        .. note::
        
        This object is composed of two methods : get and plot.
        ______________________________________________________________________
    """
    def __init__(self):
        
        self.mt = [-1,-1,-1]
        self.n_wavelet = n_wavelet
        self.az_max = az_max
        
        # Generates
        signs = np.ones([self.n_wavelet,1])
        signs[self.n_wavelet/2:] *=-1
        self.wavelets = np.tile([0.,1.,0.,-1.,0.], (self.n_wavelet, 1)) * np.tile(signs, (1, 5))
        self.obs_sph = np.asarray([np.linspace(0, az_max, self.n_wavelet),
                        np.linspace(.1,np.pi/2, self.n_wavelet),
                        np.linspace(1, 1, self.n_wavelet)])
        self.obs_cart = np.asarray(spherical_to_cartesian(self.obs_sph))
    
    def get(self, n_wavelet= 50, az_max = 8*np.pi):
        
        return self.wavelets, self.obs_sph, self.obs_cart

    def degrade(self, shift = [-.1, .1], snr = [.5, 5.]):

        self.wavelets = degrade(self.wavelets, shift,snr)
    
    def plot(self, style = '*'):
        
        plot_wavelet(self, style)


class SyntheticWavelets(object):
    """
        Set an instance of class SyntheticWavelets() that can be used to get
        synthetic wavelets.
        ______________________________________________________________________
        
        .. note::
        
        This object is composed of two methods : get and plot.
        ______________________________________________________________________
        """
    def __init__(self, n_wavelet= 100, az_max = 15*np.pi, mt=[82,5,10]):
        
        self.n_wavelet = n_wavelet
        self.az_max = az_max
        self.mt = mt
        
        t = np.linspace(.0, 1., 20, endpoint=False)
        wave = np.sin(2 * np.pi * t ) * np.sort(abs(t))[::-1]
        
        # Gets the seismic source model
        self.source = SeismicSource(mt)
        
        # Generates
        ## Template wavelets
        self.wavelets = np.tile(wave, (self.n_wavelet, 1)) #[0.,.7,.95,1.,.95,.7,0.,-.25,-.3,-.25,0.]
        ## helicoidal angles
        self.obs_sph = np.asarray([np.linspace(0, self.az_max, self.n_wavelet),
                        np.linspace(0.1, np.pi/2, self.n_wavelet),
                        np.linspace(1, 1, self.n_wavelet)])

        while len(self.obs_sph[0, self.obs_sph[0,:]>2*np.pi]) > 0:
            self.obs_sph[0, self.obs_sph[0,:]>2*np.pi] -= 2*np.pi
        
        self.obs_cart = np.asarray(spherical_to_cartesian(self.obs_sph))
        
        ## radiation pattern at given angles
        disp, xyz = self.source.Aki_Richards.radpat(wave='P',obs_sph = self.obs_sph)
        ### Direction to project
        amplitude_direction = vector_normal(xyz, 'v')
        ### Project
        disp_projected = project_vectors(disp, amplitude_direction)
        ## Norms
        amplitudes = np.sqrt(disp_projected[0]**2 + disp_projected[1]**2 + disp_projected[2]**2)
        ### Amplitudes (norm with sign)
        amplitudes *= np.sign(np.sum(disp * amplitude_direction, axis=0)+0.00001)
        
        ## Apply modeled amplitudes to artificial wavelets
        self.wavelets *= np.swapaxes(np.tile(np.sign(amplitudes),(self.wavelets.shape[1],1)),0,1)
    
    def get(self):
        
        return self.wavelets, self.obs_sph, self.obs_cart
    
    def degrade(self, shift = [-.1, .1], snr = [.5, 5.]):
        
        self.__init__(self.n_wavelet, self.az_max,self.mt)
        self.wavelets = degrade(self.wavelets, shift,snr)
    
    def plot(self, style = '*'):
        
        plot_wavelet(self, style)


class RoughDCScan(object):
    
    def __init__(self):

        self.scanned = 0
        
        # DC exploration step
        step = 10
        strikes = range(0,180,step)
        dips = range(0,90,step)
        slips = range(-180,180,step)
        
        self.modeled_amplitudes = {}
        self.p = {}
        self.t = {}
        n=0
        for Si,S in enumerate(strikes):
            for Di,D in enumerate(dips):
                for Sli,Sl in enumerate(slips):
                    
                    example = SeismicSource([S*1., D*1., Sl*1.])
                    disp, xyz = example.Aki_Richards.radpat(wave='P') #
                    
                    if n==0:
                        self.atr = cartesian_to_spherical(xyz)
                        n=1
                    
                    self.modeled_amplitudes[Si,Di,Sli] , disp_projected = disp_component(xyz, disp, 'r')
                    
                    self.p[Si,Di,Sli] = cartesian_to_spherical(example.MomentTensor.get_p_axis())
                    self.t[Si,Di,Sli] = cartesian_to_spherical(example.MomentTensor.get_t_axis())
    
    
    def scan(self, data=SyntheticWavelets()):
        
        # DC exploration step
        step = 10
        strikes = range(0,180,step)
        dips = range(0,90,step)
        slips = range(-180,180,step)
        
        SDSl = np.zeros([len(strikes)*len(dips)*len(slips),4])
        objective_function = np.zeros([len(strikes), len(dips), len(slips)])
        moment_tensors = np.zeros([len(strikes), len(dips), len(slips), 3])
        
        test = np.meshgrid( np.arange(-np.pi,np.pi, np.deg2rad(step/2.)), np.arange(0,np.pi, np.deg2rad(step/2.)) ) #sphere(n=(len(strikes)*len(dips)*len(slips))/5.)
        self.ATROpOt = [test[0], test[1], np.ones(test[1].shape) ]
        #self.ATROpOt[0] -= np.pi

        self.ATROpOt.append(np.zeros((self.ATROpOt[0]).shape))
        self.ATROpOt.append(np.zeros((self.ATROpOt[0]).shape))
        
        indexes = np.zeros([ data.wavelets.shape[0], len(self.atr[0].shape) ])
        amplitudes = np.zeros(data.wavelets[:,0].shape)
        for i,wlt in enumerate(data.wavelets):
            d = np.argmin( np.sqrt( (data.obs_sph[0,i]-self.atr[0])**2. + (data.obs_sph[1,i]-self.atr[1])**2. ))
            indexes[i,:] = np.unravel_index( d, self.atr[0].shape)

        sumcoef = [0,0]
        n=-1
        mem_rms=0
        for Si,S in enumerate(strikes):
            for Di,D in enumerate(dips):
                for Sli,Sl in enumerate(slips):
                    
                    
                    for i,wlt in enumerate(data.wavelets):
                        amplitudes[i] = self.modeled_amplitudes[Si, Di, Sli][tuple(indexes[i])]
                    
                    corrected_wavelets = np.swapaxes(np.tile(np.sign(amplitudes),(data.wavelets.shape[1],1)),0,1) * data.wavelets
                    stack_wavelets = np.sum(corrected_wavelets, axis=0)
                    rms = np.sum(stack_wavelets**2)*np.sign(np.sum(stack_wavelets))
                    
                    n+=1
                    SDSl[n,:3] = [S*1., D*1., Sl*1.]
                    SDSl[n,3] = rms
                    moment_tensors[Si, Di, Sli,:3] = [S*1., D*1., Sl*1.]
                    objective_function[Si, Di, Sli] = rms
                    
                    coef = [ np.sqrt((self.p[Si,Di,Sli][0]-self.ATROpOt[0])**2. + abs(self.p[Si,Di,Sli][1]-self.ATROpOt[1])**2.) ,
                             np.sqrt((self.t[Si,Di,Sli][0]-self.ATROpOt[0])**2. + abs(self.t[Si,Di,Sli][1]-self.ATROpOt[1])**2.) ]
                             
                    coef[0] = 1/(.1+coef[0]) ### CAN BE IMPROVED
                    coef[1] = 1/(.1+coef[1])
                    
                            
                    self.ATROpOt[3] += rms*coef[0] # [Pi,Pj] = rms
                    self.ATROpOt[4] += rms*coef[1] # [Ti,Tj] = rms

                    sumcoef[0] += np.sum(coef[0])
                    sumcoef[1] += np.sum(coef[1])

        self.ATROpOt[3] /= sumcoef[0]
        self.ATROpOt[4] /= sumcoef[1]
        
        # maximum likelyhood solution
        self.SDSl_localmax = SDSl[np.argmax(SDSl[:,3]),:]

        # 3d maximum likelyhood solution
        SDSl_likely =  np.unravel_index(np.argmax(objective_function) , objective_function.shape )
        self.SDSl_likely = moment_tensors[SDSl_likely[0], SDSl_likely[1], SDSl_likely[2], :]

        # 3d centroid solutions
        w = SDSl[:,3].copy()
        test = np.sort(w[w>0])
        test = test[ np.argmin(abs( np.cumsum(test)-np.sum(test)*.9 )) ] # centroid 90%
        #test = test[ np.argmin(abs( np.cumsum(test)-np.sum(test)*.9 )) ]
        #test = test[ int(len(test)*.98) ]
        #print np.max(w), np.max(w)/1.4, test, np.median(w[w>0]), np.std(w[w>0]), np.std(w[w>0],ddof=1)
        w[w<test] = 0. # every val below the median of positive val are cancelled
        self.SDSl_centroid = np.sum(SDSl[:,:3]*np.transpose(np.tile(w, (3,1))),axis=0)/np.sum(w)
        
        self.data = data
        self.scanned = 1
        
        #print "Scanner results"
        #print "Centroid:", self.SDSl_centroid
        #print "Max. likelyhood:", self.SDSl_localmax

    def plot(self, scanned=0, data=SyntheticWavelets()):
        
        if self.scanned == 0 or scanned == 0 :
            self.scan(data)

        # Plots
        fig = plt.figure(figsize=plt.figaspect(.5))
        ax0 = plt.subplot2grid((2,3), (0, 0), projection='3d', aspect='equal', ylim=[-1,1], xlim=[-1,1], zlim=[-1,1], title='Source model')
        ax1 = plt.subplot2grid((2,3), (0, 1), projection='3d', aspect='equal', ylim=[-1,1], xlim=[-1,1], zlim=[-1,1], title='P-axis')  #fig.add_subplot(1, 4, 2)
        ax2 = plt.subplot2grid((2,3), (1, 1), projection='3d', aspect='equal', ylim=[-1,1], xlim=[-1,1], zlim=[-1,1], title='T-axis')  #fig.add_subplot(1, 4, 3)
        ax3 = plt.subplot2grid((2,3), (0, 2), projection='3d', aspect='equal', ylim=[-1,1], xlim=[-1,1], zlim=[-1,1], title='Best model')
        ax4 = plt.subplot2grid((2,3), (1, 0), ylim=[-1,(data.n_wavelet)/100.+1.], xlim=[0,data.wavelets.shape[1]-1], xlabel='time', ylabel='Amplitude', title='Data')
        ax5 = plt.subplot2grid((2,3), (1, 2), ylim=[-1,(data.n_wavelet)/100.+1.], xlim=[0,data.wavelets.shape[1]-1], xlabel='time', ylabel='Amplitude', title='Stacked data')

        ## Pressure
        G = np.asarray(spherical_to_cartesian([self.ATROpOt[0], self.ATROpOt[1], self.ATROpOt[2]*self.ATROpOt[3]]))
        XYZ = np.asarray(spherical_to_cartesian([np.pi/2.-self.ATROpOt[0], self.ATROpOt[1], self.ATROpOt[2]]))
        plot_seismicsourcemodel(G, XYZ, comp='r', style='x', ax=ax1, cbarxlabel='P-axis likelyhood', alpha=1.)

        ## Tension
        G = np.asarray(spherical_to_cartesian([self.ATROpOt[0], self.ATROpOt[1], self.ATROpOt[2]*self.ATROpOt[4]]))
        plot_seismicsourcemodel(G, XYZ, comp='r', style='x', ax=ax2, cbarxlabel='T-axis likelyhood', alpha=1.)

        ## best sol ?
        example = SeismicSource(self.SDSl_centroid) #SDSl_localmax[:3])

        ## data points
        example.Aki_Richards.plot(wave='P', style='s', ax=ax3, cbarxlabel='Solution amplitudes')
        disp, xyz = example.Aki_Richards.radpat(wave='P', obs_sph = data.obs_sph)
        amplitudes, disp_projected = disp_component(xyz, disp, 'r')
        #corrected_wavelets = np.swapaxes(np.tile(np.sign(amplitudes),(wavelets.shape[1],1)),0,1) * wavelets
        ax3.scatter(xyz[0][amplitudes>=0],xyz[1][amplitudes>=0],xyz[2][amplitudes>=0],c='b')
        ax3.scatter(xyz[0][amplitudes<0],xyz[1][amplitudes<0],xyz[2][amplitudes<0],c='r')
        
        corrected_wavelets = np.swapaxes(np.tile(np.sign(amplitudes),(data.wavelets.shape[1],1)),0,1) * data.wavelets
        ax5.plot(np.transpose(corrected_wavelets) + np.tile(range(data.n_wavelet), (corrected_wavelets.shape[1], 1))/100.);
        
        ## Model
        data.source.Aki_Richards.plot(wave='P', style='s', ax=ax0, cbarxlabel='Modeled amplitudes')
        ## data points
        ws = np.sum(data.wavelets[:,:int(data.wavelets.shape[1]/2.)], axis=1)
        ax0.scatter(xyz[0][ws>=0],xyz[1][ws>=0],xyz[2][ws>=0],c='b')
        ax0.scatter(xyz[0][ws<0],xyz[1][ws<0],xyz[2][ws<0],c='r')
        #for i in range(n_wavelet):
        #    ax0.text(obs_cart[0][i],obs_cart[1][i],obs_cart[2][i],  '%s' % (str(i)))
        
        ax4.plot(np.transpose(data.wavelets) + np.tile(range(data.n_wavelet), (data.wavelets.shape[1], 1))/100.);
        
        
        ax3.view_init(60,40)
        ax0.view_init(60,40)
        ax2.view_init(60,40)
        ax1.view_init(60,40)
        #plt.draw()


# function skeleton
# def ggg(...):
#         """
#         Run a ...
#
#         :param type: String that specifies ... (e.g. ``'skeleton'``).
#         :param options: Necessary keyword arguments for the respective
#             type.
#
#         .. note::
#
#             The raw data is/isn't accessible anymore afterwards.
#
#         .. rubric:: _`Supported type`
#
#         ``'skeleton'``
#             Computes the ... (uses 
#               :func:`dependency.core.Class1.meth1`).
#
#         .. rubric:: Example
#
#         >>> ss.ssss('sss', ss=1, sss=4)  # doctest: +ELLIPSIS
#         <...aaa...>
#         >>> aaa.aaa()  # aaa
#
#         .. plot::
#
#             from ggg import ggg
#             gg = ggg()
#             gg.ggggg("ggggg", ggggg=3456)
#             gg.ggg()
#         """





        
