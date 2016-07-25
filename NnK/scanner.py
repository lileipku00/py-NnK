# -*- coding: utf-8 -*-
"""
source - Module for seismic sources modeling.

This module provides class hierarchy for earthquake modeling and 
 representation.
______________________________________________________________________

.. note::    
    
    Functions and classes are ordered from general to specific.

"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from obspy import read, Trace, Stream
from obspy.core.trace import Stats
from obspy.core.event.source import farfield
from obspy.imaging.scripts.mopad import MomentTensor
import copy
from mpl_toolkits.basemap import Basemap
from scipy.interpolate import griddata


   
    
def haversine(lon1=0., lat1=0., lon2=0., lat2=np.pi/2., radius=6371, phi1=None, phi2=None):
    """
    Calculates the great circle distance between two points on a sphere.
    ______________________________________________________________________
    :type radius : int | float
    :param radius :  The radius of sphere.
    
    :type lon1, lat1 : radian, float | nD np.array
    :param lon1, lat1 :  If float, the longitude and latitude of first 
        point(s, if nD np.array). 
    
    :type lon1, lat1 : radian, float 
    :param lon1, lat1 :  The longitude and latitude of end point.

    :type phi1, phi2 : radian, float | nD np.array
    :param phi1, phi2 :  Replace lat1 and lat2, which are angles from 
        equator, by specified polar angles.
    
    :rtype : idem to lon1, lat1 
    :return : great circle distance(s). Given in same unit than radius.

    .. seealso::
    
        https://en.wikipedia.org/wiki/Haversine_formula
    ______________________________________________________________________
    
    """
    if phi1 is None:
        pass
    else:
        lat1, lat2 = ( np.pi/2-phi1, np.pi/2-phi2 )
        
    lat1, lon1, lat2, lon2 = (np.asarray(lat1), np.asarray(lon1), np.asarray(lat2), np.asarray(lon2))
    if len(lon1.shape)>0:
        if lon1.shape[0]>1 and sum(lon1.shape[1:])<=1 and len(lon2.shape) == 2 :
            d3 =  tuple(np.concatenate( (np.asarray(lon2.shape)*0+1, np.asarray([len(lon1)]) )  , axis=0 ))
            d1 =  tuple(np.concatenate( (np.asarray(lon2.shape), np.asarray([1]) )  , axis=0 ))
            
            lon2 = np.repeat( np.expand_dims(lon2, axis=len(lon2.shape)), len(lon1) , axis=len(lon2.shape)) 
            lat2 = np.repeat( np.expand_dims(lat2, axis=len(lat2.shape)), len(lon1) , axis=len(lat2.shape)) 
            
            lon1 = np.tile( np.reshape(lon1, d3 ), d1 )    
            lat1 = np.tile( np.reshape(lat1, d3 ), d1 )
    
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 

    return radius * c


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
    

def globe(r=1., n=100.):

    golden_angle = np.pi * (3 - np.sqrt(5))
    theta = golden_angle * np.arange(n)
    z = np.linspace(1 - 1.0 / n, 1.0 / n - 1, n)
    radius = np.sqrt(1 - z * z)
    
    return [r * radius * np.cos(theta), r * radius * np.sin(theta), r * z]

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
        
        In origin center sphere: L: Radius, T: Parallel, Q: Meridian

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

    if v_or_h in ('Q', 'm', 'meridian', 'n', 'nhr', 'normal horizontal radial', 'norm horiz rad'): 
        ATR_n = np.array([ ATR[0] , ATR[1] - ninetydeg[0], ATR[2]])
        XYZ_n = np.asarray(spherical_to_cartesian(ATR_n))
    elif v_or_h in ('T', 'h', 'horizontal', 'horiz'): 
        ATR_n = np.array([ ATR[0] - ninetydeg[0], ATR[1]+(ninetydeg[0]-ATR[1]) , ATR[2]])
        XYZ_n = np.asarray(spherical_to_cartesian(ATR_n))
    elif v_or_h in ('v', 'vertical', 'vertical'): 
        ATR_n = np.array([ ATR[0], ATR[1]-ATR[1] , ATR[2]])
        XYZ_n = np.asarray(spherical_to_cartesian(ATR_n))
    elif v_or_h in ('L', 'r', 'radial', 'self'): 
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
        
        if abs(mt[0][0]) < abs(mt[1][0]) :
            strike, dip, rake = mt[0]
        else:
            strike, dip, rake = mt[1]
            
        #strike, dip, rake = mt[0]
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
        
        mt = MomentTensor(mt,system='XYZ') 
        
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
    
    
def plot_seismicsourcemodel(disp, xyz, style='*', mt=None, comp=None, ax=None, alpha=0.5, wave='P', cbarxlabel=None, insert_title='', cb = 1) :
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
        
        in origin center sphere: L: Radius, T: Parallel, Q: Meridian
        
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
        ax = fig.gca(projection='3d', xlabel='Lon.', ylabel='Lat.')
    ## Initializing the colorbar
    cbar=[]
    if style not in ('frame', 'wireframe') and cb == 1:
        
        axins = inset_axes(ax,
               width="5%", # width = 30% of parent_bbox
               height="60%", 
               loc=2)
            
        cbar = plt.colorbar(s_m,orientation="vertical",cax = axins)#fraction=0.07, shrink=.7, aspect=10, ax = ax)
        if cbarxlabel==None:
        	cbarxlabel = 'Displacement amplitudes'
        cbar.ax.set_ylabel(cbarxlabel)
        cbar.ax.yaxis.set_ticks_position('left')
        cbar.ax.yaxis.set_label_position('left')
    ## Initializing figure keys
    if mt is not None :
        [strike, dip, rake], [DC, CLVD, iso, deviatoric] = mt_angles(mt)
        ax.set_title(r''+wave+'-wave'+insert_title+'\n $\stackrel{' + str(int(strike)) + ', ' + str(int(dip)) + ', ' + str(int(rake)) + ' (^\circ Strike, Dip, Rake)}{' + str(int(iso)) + ', ' + str(int(DC)) + ', ' + str(int(CLVD)) + ' (\% Iso, Dc, Clvd)}$')
    
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
    return ax, cbar


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
        
    def radpat(self, wave='P', obs_cart=None, obs_sph=None):
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
            
            In origin center sphere: L: Radius, T: Parallel, Q: Meridian
            
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

        elif wave in ('Sq', 'SQ', 'Sm', 'SM', 'SN', 'Sn', 'Snrh', 'Snrh wave', 'Snrh-wave'):

            ## Get S waves
            disp, obs_cart = self.radpat(wave='S', obs_cart=obs_cart, obs_sph=obs_sph)
            ## Project on Sh component
            disp = project_vectors(disp, vector_normal(obs_cart, 'Q')) 

            return disp, obs_cart

        elif wave in ('St', 'ST', 'SH', 'Sh', 'S_h', 'Sh wave', 'Sh-wave'):

            ## Get S waves
            disp, obs_cart = self.radpat(wave='S', obs_cart=obs_cart, obs_sph=obs_sph)
            ## Project on Sh component
            disp = project_vectors(disp, vector_normal(obs_cart, 'T')) 

            return disp, obs_cart
        ######################################################################

        # Get full mt
        Mpq = mt_full(self.mt)
        

        # Get observation points
        if (obs_sph is None):
            obs_sph = sphere(r=1.,n=1000.)
        ## Get unit sphere, or spherical coordinate if given 
        if (obs_cart == None) :
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

    def plot(self, wave='P',style='*', comp=None, ax=None, cbarxlabel=None, insert_title='', cb=1) :
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

            In origin center sphere: L: Radius, T: Parallel, Q: Meridian
            
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
                comp='Q'
            elif wave in ('Sq', 'SQ', 'Sm', 'Sn', 'Snrh','Snrh wave', 'Snrh-wave'):
                comp='Q'
            elif wave in ('ST', 'St', 'Sh', 'Sh wave', 'Sh-wave'):
                comp='T'
            elif wave in ('P', 'P wave', 'P-wave'):
                comp='L'

        return plot_seismicsourcemodel(G, XYZ, style=style, mt=self.mt, comp=comp, ax=ax, wave=wave, cbarxlabel=cbarxlabel, insert_title=insert_title, cb =cb)

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
        
    def radpat(self, wave='P', obs_cart=None, obs_sph=None):
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
        if obs_cart == None :
            obs_cart = spherical_to_cartesian(sphere(r=1.,n=1000.))
        ## Get unit sphere, or spherical coordinate if given 
        if obs_sph == None :
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
        
        elif wave in ('ST', 'St', 'SH', 'Sh', 'Sh-wave', 'Sh wave', 'SH-wave', 'SH wave'):
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
        return plot_seismicsourcemodel(G, XYZ, style=style, mt=self.mt, comp='L',ax=ax, cbarxlabel=cbarxlabel)

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

    def __init__(self, mt=[10,5,82], poisson=0.25):        
        self.MomentTensor = MomentTensor(mt, system='XYZ',debug=2)
        self.Aki_Richards = Aki_Richards(np.asarray(self.MomentTensor.get_M(system='XYZ')))  
        self.Vavryeuk     = Vavryeuk(np.asarray(self.MomentTensor.get_M(system='XYZ')),poisson = poisson)
        
        c=2
        lv = np.array([0,c/2,0,0.,0.,0.])  
        iso = np.array([c/2.0001,c/2.000001,c/2.0000000001,0.,0.,0.]) * 1./np.sqrt(3.) 
        dc = np.array([0.,0.,0.,np.sqrt(c),0.,0.]) * 1./np.sqrt(2.) 
        clvd = np.array([-c,c/2,c/2,0.,0.,0.]) * 1./np.sqrt(6.) 
        
        
        self.simple_models={'lv': {'definition':lv, 'name':'Linear vector'},
                            'iso': {'definition':iso, 'name':'Isotropic'}, 
                            'clvd': {'definition':clvd, 'name':'Compensated linear vector'},
                            'dc': {'definition':dc, 'name':'Double couple'} }
    
    def demo(self):
        
        # Axes Plots
        fig = plt.figure(figsize=plt.figaspect(1.))
        p = ((0,0), (1,0), (0,1), (1,1)) 
        cb=[0,0,0,1]
        for i,v in enumerate(self.simple_models.keys()):
            ax = plt.subplot2grid((2,2), p[i], projection='3d', aspect='equal', ylim=[-1,1], xlim=[-1,1], zlim=[-1,1]) 
            example = SeismicSource(self.simple_models[v]['definition']) 
            example.Aki_Richards.plot(wave='P', style='*', ax=ax, cbarxlabel='P-wave amplitudes', cb=cb[i])  
            ax.set_title(self.simple_models[v]['name']) 
            
        plt.tight_layout()
        
        

def sphere2basemap(map, azimuthangle_polarangle_radialdistance):
    
    azimuth =  450. - np.rad2deg(azimuthangle_polarangle_radialdistance[0])
    takeoff =   90. - np.rad2deg(azimuthangle_polarangle_radialdistance[1])
    #radius = azimuthangle_polarangle_radialdistance[2]
    
    while len(takeoff[takeoff>90.])>0 or len(takeoff[takeoff<-90.])>0 :
        
        azimuth[takeoff <-90.] += 180.
        takeoff[takeoff <-90.] += 180.
        
        azimuth[takeoff  >90.] += 180.
        takeoff[takeoff  >90.] -= 180.
    
    
    while len(azimuth[azimuth>360.])>0 or len(azimuth[azimuth<0.])>0 :
        
        azimuth[azimuth   <0.] += 360.
        azimuth[azimuth >360.] -= 360.
        
       
    return map( azimuth, takeoff )



def degrade(wavelets, shift = [-.1, .1], snr = [.5, 5.]):
    
    shift = np.random.random_integers(int(shift[0]*1000), int(shift[1]*1000), len(wavelets))/1000. # np.linspace(shift[0], shift[1], wavelets.shape[0])
    snr = np.random.random_integers(int(snr[0]*1000), int(snr[1]*1000), len(wavelets))/1000. # np.linspace(snr[0], snr[1], wavelets.shape[0])
    
    for i,w in enumerate(wavelets):
        w = w.data
        tmp = np.max(abs(w)).copy()
        wavelets[i].data += (np.random.random_integers(-100,100,len(w))/100.) * np.max(w)/snr[i]
        wavelets[i].data /= tmp #*np.max(abs(self.wavelets[i]))
        
        tmp = np.zeros( len(w)*3. )
        index = [ int(len(w)+(shift[i]*len(w))), 0 ]
        index[1] = index[0]+len(w)
        tmp[index[0]:index[1]] = wavelets[i].data[:int(np.diff(index)) ]
        wavelets[i].data[-len(w):] = tmp[-2*len(w):-len(w)]
    
    return wavelets

def plot_wavelet(bodywavelet, style = '*', ax=None, detail_level = 1):
    
    ## Initializing the plot
    if ax == None:
         ax = (plt.figure(figsize=plt.figaspect(1.))).gca(projection='3d')
                
    axins = inset_axes(ax,
                   width="60%", # width = 30% of parent_bbox
                   height="30%", 
                   loc=3)
    
    axins.patch.set_alpha(0.5)

    if hasattr(bodywavelet, 'SeismicSource'):
        ax, cbar = bodywavelet.SeismicSource.Aki_Richards.plot(wave='P', style='s', ax=ax, insert_title=" and "+bodywavelet.title)
    
    wavelets = []
    ws = [] 
    lmax = 0
    for i,w in enumerate(bodywavelet.Stream):
        #print bodywavelet.Stream[i].data.shape
        wavelets.append(w.data)
        ws.append( np.sum( w.data[:int(len(w.data)/2.)]) )
        lmax = np.max([ lmax , len(w.data) ])
        axins.plot(w.data+i/100.)
    
    axins.set_xlim([0 , lmax-1])
    axins.yaxis.set_ticks_position('left')
    axins.yaxis.set_label_position('left')
    axins.set_xlabel('Time samples')
    axins.set_ylabel('Amplitudes')

    
    wavelets = np.ascontiguousarray(wavelets)
    ws = np.ascontiguousarray(ws)
 
    ax.scatter(bodywavelet.observations['cart'][0][ws>=0.],
                bodywavelet.observations['cart'][1][ws>=0.],
                bodywavelet.observations['cart'][2][ws>=0.],
                marker='+', c='b')
    ax.scatter(bodywavelet.observations['cart'][0][ws<0.],
                bodywavelet.observations['cart'][1][ws<0.],
                bodywavelet.observations['cart'][2][ws<0.],
                marker='o', c= 'r')
    
    
            
    if detail_level == 2:        
        for i in range(bodywavelet.observations['n']):
            ax.text(bodywavelet.observations['cart'][0][i],
                     bodywavelet.observations['cart'][1][i],
                     bodywavelet.observations['cart'][2][i],
                     '%s' % (str(i)))     
            
    
    #ax.set_xlabel('Lon.')
    ax.set_ylabel('Lat.')
    ax.set_zlabel('Alt.')
    
    ax.set_xticks(ax.get_xticks()[[1]])
    ax.set_yticks(ax.get_yticks()[[1,-2]])
    ax.set_zticks(ax.get_zticks()[[1,-2]])

#     ticks = [ax.xaxis.get_major_ticks(), ax.yaxis.get_major_ticks(), ax.zaxis.get_major_ticks()]
#     for j, axticks in enumerate(ticks):
#         for i,tick in enumerate(axticks):
#             if i != 0 and i != len(axticks)-1:
#                 tick.label.set_visible(False)

#     ax.tick_params(axis='both',          # changes apply to the x-axis
#                      which='both',      # both major and minor ticks are affected
#                      right='off',      # ticks along the bottom edge are off
#                      left='off',         # ticks along the top edge are off
#                      top='off',      # ticks along the bottom edge are off
#                      bottom='off',         # ticks along the top edge are off
#                      labelbottom='off',
#                      labelleft='off',
#                      labelright='off')
    
    if detail_level==0:
        axins.tick_params(axis='both',          # changes apply to the x-axis
                         which='both',      # both major and minor ticks are affected
                         right='off',      # ticks along the bottom edge are off
                         left='off',         # ticks along the top edge are off
                         top='off',      # ticks along the bottom edge are off
                         bottom='off',         # ticks along the top edge are off
                         labelbottom='off',
                         labelleft='off',
                         labelright='off' )

    return ax, axins, cbar

class ArticialWavelets(object):
    """
        Set an instance of class ArticialWavelets() that can be used to get
        artificial wavelets.
        ______________________________________________________________________
        
        .. note::
        
        This object is composed of two methods : get and plot.
        ______________________________________________________________________
    """
    def __init__(self, n_wavelet= 50, az_max = 8*np.pi):
        
        self.mt = [-1,-1,-1]
        self.n_wavelet = n_wavelet
        self.az_max = az_max
        
        # Generates
        signs = np.ones([self.n_wavelet,1])
        signs[self.n_wavelet/2:] *=-1
        self.wavelets = np.tile([0.,1.,0.,-1.,0.], (self.n_wavelet, 1)) * np.tile(signs, (1, 5))
        self.obs_cart = np.asarray(globe(n=n_wavelet))
        self.obs_sph = np.asarray(cartesian_to_spherical(self.obs_cart))
    
    def get(self):
        
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
        :type self : object: 
        :param self : 
        
            self.Stream
            self.observations {'n_wavelet'
                               'mt'
                               'types'
                               'cart'
                               'sph'
             
            self.MomentTensor : optional, 
            self.SeismicSource : optional,  
            
        
        .. note::
        
        This object is composed of two methods : get and plot.
        
        .. TODO::
        put all of this in a obspy stream
        ______________________________________________________________________
        """
    def __init__(self, n = 50, mt=None, full_sphere=0, gap = 0):
                
        if mt == None :
            mt = [np.random.uniform(0,360) ,np.random.uniform(-90,90),np.random.uniform(0,180)]
        
        current_gap = 0 
          
        # Gets the seismic source model
        self.SeismicSource = SeismicSource(mt)
        self.MomentTensor = MomentTensor(mt,system='XYZ',debug=2)

        # 
        if full_sphere == 1 :
            n_sph = n
        else:
            n_sph = n*2
        
        # get sphere points, make it half if needed, sorts along last axis
        obs = (np.asarray(globe(n=n_sph)))[:, :n]        
        
        if gap > 0:
            if gap > np.pi:
                gap = np.deg2rad(gap)
            current_n = n
            N_cum = n_sph-1
            n_cum = n
            while ((current_gap < gap) or (current_n < n)):
                N_cum += 1
                obs = np.asarray(globe(n=N_cum))           
                                  
                if full_sphere != 1 :
                    obs = obs[:, :int(N_cum/2.)]
                
                obs = np.array([ obs[i,:] for i in [2,1,0] ])
                
                obs = obs[:, cartesian_to_spherical(obs)[1][:]>gap/2. ]
                
                if obs.size > 0:                  
                    current_gap = np.min(cartesian_to_spherical(obs)[1][:])*2
                    current_n = obs.shape[1]
                    
                obs = np.array([ obs[i,:] for i in [2,1,0] ])
        
        n=obs.shape[1]
        self.title = 'observations'
        self.observations = {'types': np.tile('P', (n, 1)),
                             'cart' : obs,
                             'sph'  : np.asarray(cartesian_to_spherical( obs )),
                             'mt'   : mt,
                             'n'    : n, 
                             'gap'  : current_gap }
        
        # Generates template wavelets #####################
        t = np.linspace(.0, 1., 20, endpoint=False)
        wave = np.sin(2 * np.pi * t )  
        wavelets = np.tile(wave, (n , 1)) 
        
        ## radiation pattern at given angles
        source_model = SeismicSource( mt )
        disp, observations_xyz = source_model.Aki_Richards.radpat(wave='P', obs_sph = self.observations['sph'] )                   
        #disp = farfield( np.ravel(self.MomentTensor.get_M())[[0,4,8,1,2,5]] , self.observations['cart'] , 'P')
        amplitudes, disp_projected = disp_component(self.observations['cart'], disp, 'r')

        ## Apply modeled amplitudes to artificial wavelets
        wavelets *= np.swapaxes(np.tile(np.sign(amplitudes),(wavelets.shape[1],1)),0,1)
        
        #
        self.Stream = Stream()        
        for i in range(n):
            self.Stream.append(Trace(data=wavelets[i,:] , 
                                     header=Stats({'network' : "SY",
                                                   'station' : str(i),
                                                   'location': "00",
                                                   'channel' : "EHL",   # in origin center sphere: L: Radius, T: Parallel, Q: Meridian
                                                   'npts'    : len(t),
                                                   'delta'   : 1/((t[-1]-t[0])/len(t)) }) ))        
        
    def get(self):
        
        return self
    
    def degrade(self, shift = [-.1, .1], snr = [.5, 5.]):
        
        #self.__init__(self.observations['n'], self.observations['mt'])

        self.Stream = degrade( self.Stream , shift, snr)
                
            
    def plot(self, style = '*'):
         
        return plot_wavelet( self, style)


class BodyWavelets(object):
    """
        Set an instance of class SyntheticWavelets() that can be used to get
        synthetic wavelets.
        ______________________________________________________________________
    
        .. note::
        
        This object is composed of two methods : get and plot.
        ______________________________________________________________________
        """
    def __init__(self, f= 100., starts=-0.05, ends=0.2, n_wavelet= 50, sds= "/Users/massin/Documents/Data/ANT/sds/", catalog = "/Users/massin/Desktop/arrivals-hybrid.Id-Net-Sta-Type-W_aprio-To-D-Az-Inc-hh-mm-t_obs-tt_obs-tt_calc-t_calc-res-W_apost-F_peak-F_median-A_max-A_unit-Id-Ot-Md-Lat-Lon-Dep-Ex-Ey-Ez-RMS-N_P-N_S-D_min-Gap-Ap-score_S-score_M", sacs= "/Users/massin/Documents/Data/WY/dtec/2010/01/21/20100121060160WY/", nll = "//Users/massin/Documents/Data/WY/dtec/2010/01/21/20100121060160WY/20100121060160WY.UUSS.inp.loc.nlloc/WY_.20100121.061622.grid0.loc.hyp", mode="sds-column"):

        from obspy.core.stream import read

        self.n_wavelet = n_wavelet
        self.az_max = []
        self.mt = []
        self.wavelets = np.asarray([])
        self.obs_sph = np.asarray([])
        npoints = f*(ends - starts)-1
        
        
        if mode == "sds-column" :
            
            from obspy.core.utcdatetime import UTCDateTime
            from obspy.clients.filesystem.sds import Client

            client = Client(sds)

            names=('Networks','Stations','Waves', 'weights','Origin time', 'Distances', 'Azimuth', 'Takeoff', 'Hours', 'Minuts', 'Seconds', 'Magnitudes', 'Id')
            columns=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 23, 0)
            metadata = np.genfromtxt(catalog, usecols=columns, comments="Id", names=names, dtype=None)

            for arrival,md in enumerate(metadata):
                if metadata[arrival][5] > 1. and self.wavelets.shape[0] < n_wavelet :
                    
                    time = "%17.3f" % metadata[arrival][4]
                    time = UTCDateTime(time[:8]+'T'+time[8:])
                    time += (metadata[arrival][8]-time.hour)*60*60 + \
                        (metadata[arrival][9]-time.minute)*60 + \
                        (metadata[arrival][10]-(time.second+time.microsecond/1000000.))
                    
                    st = client.get_waveforms(metadata[arrival][0], metadata[arrival][1], "*", "*[Z]", time+2*starts, time+2*ends) #
                    #st.trim(time+starts, time+ends)
                    st.detrend()
                    st.normalize()
                    st.interpolate(f, starttime=time+starts, npts=npoints)
                    for t,Trace in enumerate(st):
                        if self.wavelets.shape[0] < n_wavelet :
                            
                            data = np.zeros((1,npoints))
                            data[:] = Trace.data[:npoints]
                            angles = np.zeros((1,3))
                            angles[:] = ([ np.deg2rad(metadata[arrival][6]), np.deg2rad(metadata[arrival][7]), 1.0]) # metadata[arrival][5]])
                            if  self.wavelets.shape[0] == 0 :
                                self.wavelets = data
                                self.obs_sph = angles
                            else :
                                self.wavelets = np.concatenate((self.wavelets, data), axis=0)
                                self.obs_sph =  np.concatenate((self.obs_sph, angles), axis=0)

        elif mode == "sac-nll" :
            
            from obspy import read_events
            import glob
            cat = read_events(nll)
            
            for p,pick in enumerate(cat[0].picks):
                if self.wavelets.shape[0] < n_wavelet :
                    #print pick.waveform_id, pick.phase_hint, pick.time,
                    for a,arrival in enumerate(cat[0].origins[0].arrivals):
                        if arrival.pick_id == pick.resource_id:
                            #print arrival.azimuth, arrival.takeoff_angle, arrival.distance
                            seismic_waveform_file = sacs+"*"+pick.waveform_id.station_code+"*Z*.sac.linux"
                            if len(glob.glob(seismic_waveform_file))>0:
                                st = read(seismic_waveform_file)
                                st.detrend()
                                st.normalize()
                                st.interpolate(f, starttime=pick.time+starts, npts=npoints)
                                for t,Trace in enumerate(st):
                                    if self.wavelets.shape[0] < n_wavelet :
                                        
                                        data = np.zeros((1,npoints))
                                        data[:] = Trace.data[:npoints]/np.max(abs(Trace.data[:npoints]))
                                        angles = np.zeros((1,3))
                                        angles[:] = ([ np.deg2rad(arrival.azimuth), np.deg2rad(arrival.takeoff_angle), 1.0]) # metadata[arrival][5]])
                                        if  self.wavelets.shape[0] == 0 :
                                            self.wavelets = data
                                            self.obs_sph = angles
                                        else :
                                            self.wavelets = np.concatenate((self.wavelets, data), axis=0)
                                            self.obs_sph =  np.concatenate((self.obs_sph, angles), axis=0)
                                            
        self.obs_sph = (self.obs_sph.T)
        self.obs_cart = np.asarray( spherical_to_cartesian(self.obs_sph))
        self.n_wavelet = self.wavelets.shape[0]

    def get(self):
        
        return self.wavelets, self.obs_sph, self.obs_cart

    def degrade(self, shift = [-.1, .1], snr = [.5, 5.]):
        
        self.__init__(self.n_wavelet, self.az_max,self.mt)
        self.wavelets = degrade(self.wavelets, shift,snr)

    def plot(self, style = '*'):
        
        plot_wavelet(self, style)



class SourceScan(object):

    '''
        .. To do : 
            [x] use obspy stream
            [x] use predefined grids
            [X] separate pdf plot (richer)
            [X] spherical interpolation 
            [|] use obspy.core.event.source.farfield  | obspy.taup.taup.getTravelTimes
            [|] linear scan
    '''
    
    def __init__(self, n_model = 1500, 
                 n_obs=2000, 
                 n_dims=3, 
                 waves = ['P', 'S'], 
                 components = [['L'], ['T', 'Q'] ], 
                 grids_rootdir='~/.config/seismic_source_grids',
                 grid=''):
        '''
            Sets model space
        '''
        
        ## Attributes info 
        s = '_'
        self.file = grids_rootdir+'/Wtypes_'+s.join(waves)+'.Ch_'+s.join(sum(components, []))+'.Nd_'+str(n_dims)+'.Nm_'+str(n_model)+'.No_'+str(n_obs)+'.npz'
        self.grids_rootdir = grids_rootdir
        self.n_model = n_model
        self.n_obs = n_obs
        self.n_dims = n_dims
        ## Wave types
        self.waves = waves
        self.components = components # in origin center sphere: L: Radius, T: Parallel, Q: Meridian
        
        ## Initial grids for modeling
        ### Observations (in trigo convention)
        self.atr = cartesian_to_spherical(globe(n=n_obs)) 
        observations_atr_nparray = np.asarray(self.atr)
#         # test plot ##################################################
#         ax = (plt.figure()).gca(projection='3d')                     #
#         ax.scatter(globe(n=500)[0], globe(n=500)[1], globe(n=500)[2])#
#         ##############################################################

        if n_dims == 3 :
            # Scans : strike, dip, slip
            
            ## DC exploration step
            self.precision = ((180.**3.)/n_model)**(1/3.)
            
            strikes = np.arange(0,180, self.precision) 
            dips = np.arange(0,90, self.precision) 
            slips = np.arange(-180,180, self.precision)
            
            ## Sources (any convention of MoPad can be used)
            source_mechanisms = np.asarray(  np.meshgrid(strikes, dips, slips)  )*1.  #, sparse=True
            source_mechanisms = source_mechanisms.transpose( np.roll(range(len(source_mechanisms.shape)),-1) )
            
        elif n_dims == 4 :
            # Scans: strike, dip, slip, DC%
            print "S, D, Sl, DC% scan not yet impl"
            
        elif n_dims == 5 :            
            # Scans: strike, dip, slip, DC%, ISO%
            print "strike, dip, slip, DC%, ISO%  scan not yet impl"
            
        elif n_dims == 6 :            
            # Scans: Sxx, Syy, Szz, Sxy, Sxz, Syz
            print "full mt scan not yet impl"
            
        N = np.prod(source_mechanisms.shape[:-1])
        flat2coordinate = np.asarray( np.unravel_index( range(N), source_mechanisms.shape[:-1] ) )        
        
        # Machinery
        self.scanned = 0        
        if not os.path.exists(os.path.expanduser(grids_rootdir)):
            os.makedirs(os.path.expanduser(grids_rootdir))
        file = os.path.expanduser(self.file)
        
        # Test if grids exists 
        if not os.path.exists(file) or grid is 'reset':
                        
            # Initiates
            self.modeled_amplitudes = {}
            self.source_mechanisms = {'Mt'      : np.zeros([N,len(source_mechanisms.shape)-1]) , 
                                      'fullMt'  : np.zeros([N,6]), 
                                      'P-axis'  : np.zeros([N,3]), 
                                      'T-axis'  : np.zeros([N,3]), 
                                      'rms'     : np.zeros(N), 
                                      'xcorr'   : np.zeros(N),
                                      'P(d|Mt)' : np.zeros(N),
                                      'P(Mt|d)' : np.zeros(N), 
                                      'P(d)'    : np.zeros(N), 
                                      'P(Mt)'   : np.ones(N)*2./N } # only half of the models are really differents (point symetry)
            
            ## Loops over models #
            for i in range(N):   #            
                source_model = SeismicSource( source_mechanisms[ tuple(flat2coordinate[:,i]) ])
                
                sm = tuple(source_mechanisms[ tuple(flat2coordinate[:,i]) ])
    
                self.source_mechanisms[    'Mt'][i,:] = np.asarray(sm)
                
                # ISSUE: 
                # MomentTensor.get_M and MomentTensor.get_DC output non DC parts even for pure DC input with 90 deg multiple !!!
                self.source_mechanisms['fullMt'][i,:] = np.ravel(np.asarray(source_model.MomentTensor.get_M(system='XYZ')))[[0,4,8,3,6,7]]
                #self.source_mechanisms['fullMt'][i,:] = np.ravel(np.asarray(source_model.MomentTensor.get_DC(system='XYZ')))[[0,4,8,3,6,7]]    
                    
                self.source_mechanisms['P-axis'][i,:] = cartesian_to_spherical(source_model.MomentTensor.get_p_axis(system='XYZ'))
                self.source_mechanisms['T-axis'][i,:] = cartesian_to_spherical(source_model.MomentTensor.get_t_axis(system='XYZ'))
                           
                ### Loops over wave types ##########
                for wi,w in enumerate(self.waves): #
                    displacement_xyz, observations_xyz = source_model.Aki_Richards.radpat(wave=w, obs_sph = self.atr)
                
                    #### Loops over components of waves #########
                    for ci,c in enumerate(self.components[wi]): #         
                        self.modeled_amplitudes[ sm, w, c ], disp_projected = disp_component(observations_xyz, displacement_xyz, c) 
                        
#                         # tests amplitudes values #####################################################
#                         ax, cbar = source_model.Aki_Richards.plot(style='*', insert_title='('+c+' compo)', wave=w) 
#                         plus = self.modeled_amplitudes[ sm, w, c ]>0
#                         minus = self.modeled_amplitudes[ sm, w, c ]<=0
#                         ax.plot(displacement_xyz[0][plus], 
#                                 displacement_xyz[1][plus], 
#                                 displacement_xyz[2][plus], '+b')   #
#                         ax.plot(displacement_xyz[0][minus], 
#                                 displacement_xyz[1][minus], 
#                                 displacement_xyz[2][minus], 'or')   #
#                         if w=='S' and c=='m':
#                             return #######################################################################
                
#                         # re-indexes each obs point by sph. coordinate in rad ###############
#                          for line in range(observations_atr_nparray.shape[1]):              #
#                              #for col in range(observations_atr_nparray.shape[2]):          #
#                              obs_atr = tuple(observations_atr_nparray[:,line])              #
#                              self.modeled_amplitudes[ obs_atr, sm, w, c ] = amplitudes[line]#
#                              #print '[',obs_atr, sm, w, c,']=',amplitudes[line]##############
                  
                 
            ### Saves for next time   
            print 'Saving',file
            np.savez(file, source_mechanisms = self.source_mechanisms, modeled_amplitudes=self.modeled_amplitudes)
        else:
            print 'Loading',file
            npzfile = np.load(file)
            self.modeled_amplitudes = npzfile['modeled_amplitudes'].item()
            self.source_mechanisms  = npzfile['source_mechanisms'].item()
        
        print 'Loaded in object:',  
        print N,'source models (precision:',self.precision,') for',
        print np.prod(np.asarray(self.atr[0]).shape), 'observations',
        print len(waves),'waves',
        print len(sum(components, [])),'components.'
        #for key, value in self.modeled_amplitudes.iteritems():
        #   print key, value

        
    def _data_init(self, data):
        '''
            Sets data indexes in model space                 
        '''        
        
        # Initiate ######################
        self.data = data #
        self.data_wavelets = []         #
        self.data_taperwindows = []     #
        #################################
        
        # Makes array with data with corresponding taper ########
        lm = 0                                                  #
        for i,w in enumerate(data.Stream):                      #
            l = len(w.data)                                     #
            # stores wavelet ####################################
            self.data_wavelets.append(w.data/np.max(abs(w.data)))
            # prepare taper #####################################
            taper = 2.*(1+(np.sort(range(l))[::-1]))            #
            taper[taper>l] = l                                  #
            taper /= l                                          #
            # stores taper ######################################
            self.data_taperwindows.append(taper)                #
            # stores max len ####################################
            lm = np.max([lm, l])                                #                             
            if lm>l :                                           #
                im = i                                          #
        #########################################################
        
        # Machinery #####################################################
        self.data_wavelets = np.asarray(self.data_wavelets)             #  
        self.data_amplitudes = np.asarray(self.data_wavelets)*0.        #
        #################################################################

        # get observation indexes corresponding to model space ##
        self.data_indexes = np.zeros([ self.data_wavelets.shape[0], len(self.atr[0].shape) ], dtype=np.int32)
        for i in range(len(data.Stream)):                       #
            distances = np.sqrt( (data.observations['sph'][0,i]-self.atr[0])**2. + (data.observations['sph'][1,i]-self.atr[1])**2. + (data.observations['sph'][2,i]-self.atr[2])**2. )
            d = np.argmin(distances)
            self.data_indexes[i,:] = np.unravel_index( d, self.atr[0].shape)
#             if np.rad2deg(np.min( distances )) > 10: 
#                 print "Warning: unreliable amplitude modeling for station", data.Stream[i].stats.station 
        ##########################################################
        
        # search brute optimal stack #########
        opt_stack = np.zeros((9999))   #
        ## loops over trace ##############################
        for w,wavelet in enumerate(self.data_wavelets):  #
            l = len(wavelet)                             #
            if np.sum((opt_stack[:l]+wavelet*self.data_taperwindows[w]*-1)**2.) > np.sum((opt_stack[:l]+wavelet*self.data_taperwindows[w])**2.):
                opt_stack[:l] += wavelet*self.data_taperwindows[w]*-1 
            else:                                                 
                opt_stack[:l] += wavelet*self.data_taperwindows[w]
        ##################################################
        
        
        # make theoretical optimal stack ##########################
        t = np.linspace(.0, 1., lm, endpoint=False)               #
        synth_stack = np.sin(2 * np.pi * t ) * len(self.data_wavelets) * self.data_taperwindows[i]    #       Warning: optimal stack is tapered !!!!        
        ###########################################################

        # stores optimal stacks ################################
        self.synth_stack = synth_stack[:lm]              # Warning: optimal stack is tapered !!!!        
        self.power_synth_stack = np.nansum((synth_stack)**2.) #
        self.opt_stack = opt_stack[:lm]              # Warning: optimal stack is tapered !!!!        
        self.power_opt_stack = np.nansum((opt_stack)**2.) #
        #######################################################
        
        self.model_perfectmodel_corr = (len(np.unique(self.data_indexes[self.data_indexes+1<=self.atr[0].size/2.]))*1./self.atr[0].size)
        self.model_perfectmodel_corr = np.nanmin([1., self.model_perfectmodel_corr])
        
#         # test plot ################################
#         ax = (plt.figure()).gca()                  #
#         ax.plot(np.transpose(self.data_wavelets))  #
#         ax.plot(self.data_optimal_stack)           #
#         ############################################
    
    
    def scan(self, data=SyntheticWavelets(mt=None), centroid=1., info=0):
        '''
            Explore the model space with given data.
            
            data.Stream
            data.observations {'n_wavelet'
                               'mt'
                               'types'
                               'cart'
                               'sph'
             
            data.MomentTensor : optional, 
            data.SeismicSource : optional, 
        '''
        
        #print data.observations['mt']
        # Get : ########################
        #   - optimal data stack       #
        #   - model's indexes for data #
        self._data_init(data)          #
        ################################

        # Scans source ### how to make it linear ? #############
        globaldist_opt_stack = 0.
        #stacks = np.zeros([self.source_mechanisms['Mt'].shape[0],len(self.opt_stack)])
        for i in range(self.source_mechanisms['Mt'].shape[0]): #
            
            Mo = self.source_mechanisms['Mt'][i,:]

            # gets pdf value #################################
            for j,wavelet in enumerate(self.data_wavelets):  #
                self.data_amplitudes[j][:] = self.modeled_amplitudes[ tuple(Mo), 
                                                                      data.observations['types'][j,0], 
                                                                      data.Stream[j].stats.channel[-1] ][ tuple(self.data_indexes[j]) ]
                            
            corrected_wavelets = np.sign(self.data_amplitudes) * self.data_wavelets * self.data_taperwindows 
            stack_wavelets = np.nansum(corrected_wavelets, axis=0)
            self.source_mechanisms['rms'][i] = np.nansum(stack_wavelets**2)*np.sign(np.nansum(stack_wavelets))
            self.source_mechanisms['xcorr'][i] = (np.corrcoef(self.opt_stack, stack_wavelets))[0,1]
            
            #stacks[i,:] = self.opt_stack-stack_wavelets
            globaldist_opt_stack += np.nansum((self.opt_stack - stack_wavelets)**2)
            ##################################################
        
        self.source_mechanisms['xcorr'][self.source_mechanisms['rms']==0.] = 0
                                           
        # get probabilities 
        ## P to get the current data for a given Mt
        self.source_mechanisms['P(d|Mt)'] = self.source_mechanisms['rms'] / self.power_synth_stack #power_optimal_stack power_brute_opt_stack
                
        ## P to get the current data overall
        self.source_mechanisms['P(d)']  = (np.nansum(np.abs(self.source_mechanisms['rms'])>=np.nanmax(self.source_mechanisms['rms']))*.5/len(self.source_mechanisms['rms'])) # *2/np.pi
        if info ==1:
            print "P(d), prelim",self.source_mechanisms['P(d)']
        
#         self.source_mechanisms['P(d)']  *= (self.power_opt_stack-np.nanmax(abs(self.source_mechanisms['rms'])))/self.power_opt_stack
# #       self.source_mechanisms['P(d)']  += 1.-self.model_perfectmodel_corr
#         if info ==1:
#             print "      correction", (self.power_opt_stack-np.nanmax(abs(self.source_mechanisms['rms'])))/self.power_opt_stack
        
        # echelle ok, evolue mal en gap
        #len(self.source_mechanisms['rms'])*len(self.opt_stack)/self.source_mechanisms['P(d)']
        # evolue bien, mais pas a l'echelle:
        #np.nanstd((self.power_opt_stack-self.source_mechanisms['rms'])/len(self.opt_stack))#**2
        
        
        # limits impossibles values
        # must be np.nanmin(self.source_mechanisms['P(Mt)'])  < < np.nanmax(self.source_mechanisms['P(d|Mt)']) ????        
        self.source_mechanisms['P(d)'] = np.max([self.source_mechanisms['P(d)'], np.nanmin(self.source_mechanisms['P(Mt)']) ])
        self.source_mechanisms['P(d)'] = np.min([self.source_mechanisms['P(d)'], np.nanmax(self.source_mechanisms['P(d|Mt)']) ])
#         self.source_mechanisms['P(d)'] = np.nanmin([self.source_mechanisms['P(d)'], 
#                                                     np.nanmin(self.source_mechanisms['P(d|Mt)'] * self.source_mechanisms['P(Mt)']) ])
        
        ## P to get the Mt for the given data
        self.source_mechanisms['P(Mt|d)'] = self.source_mechanisms['P(d|Mt)'] * self.source_mechanisms['P(Mt)'] / self.source_mechanisms['P(d)']
        
        
        # Gets brightest cell
        self.best_likelyhood = [self.source_mechanisms['Mt'][np.argmax(self.source_mechanisms['P(Mt|d)'])], 
                                np.nanmax(self.source_mechanisms['P(Mt|d)']) ]
        
        # Gets full Mt centroid   
        ## reshape & repeat for fullMt's dimensions    
        repeat_rms = np.repeat(np.expand_dims(self.source_mechanisms['P(Mt|d)'], 
                                         axis=len(self.source_mechanisms['rms'].shape)), 
                         self.source_mechanisms['fullMt'].shape[1] , 
                         axis=len(self.source_mechanisms['rms'].shape)) 
        ## voids negative part
        repeat_rms[repeat_rms<0.] = 0.
        ## voids flat part
        #lim = (np.sort(self.source_mechanisms['P(Mt|d)']))[int(len(self.source_mechanisms['P(Mt|d)'])*centroid)]
        lim = np.nanmean(repeat_rms)+centroid*np.std(repeat_rms)
        repeat_rms[repeat_rms<lim] = 0.
        ## weighted average 
        self.centroid = [(np.nansum(repeat_rms * self.source_mechanisms['fullMt'], axis=0)) / (np.nansum(repeat_rms, axis=0)) / 1. , 0 ]
        ## no nan
        self.centroid[0][np.isnan(self.centroid[0])] = 0.00000000001
        ## gets corresponding  probability
        self.centroid[1] = (self.corrected_data(self.centroid[0], self.data, title='')).observations['P(Mt|d)']
        
        # Important
        self.scanned = 1
        
        if info ==1:
            print 'P(d)', self.source_mechanisms['P(d)']
            print 'P(Mt)', np.nanmin(self.source_mechanisms['P(Mt)']), np.nanmax(self.source_mechanisms['P(Mt)'])
            print 'P(d|Mt)', np.nanmin(self.source_mechanisms['P(d|Mt)']), np.nanmax(self.source_mechanisms['P(d|Mt)'])
            print 'P(Mt|d)', np.nanmin(self.source_mechanisms['P(Mt|d)']), np.nanmax(self.source_mechanisms['P(Mt|d)']) 
            print 'best likelyhood', self.best_likelyhood, '(full mt, P(Mt|d)%)'
            print 'centroid', self.centroid, '(full mt, P(Mt|d)%)'
    
    def plot(self, scanned=1, data=SyntheticWavelets(mt=None), sol = None, style = '*'):
                
        if self.scanned == 0 or scanned == 0 :
            self.scan(data)

        # Plots
        fig = plt.figure(figsize=(9,9))
        ax1 = plt.subplot2grid((2,2), (0, 0), projection='3d')
        ax2 = plt.subplot2grid((2,2), (1, 0), projection='3d')
        ax3 = plt.subplot2grid((2,2), (1, 1), projection='3d')
        ax4 = plt.subplot2grid((2,2), (0, 1))
        
        ## plots data
        ax, axins, cbar = plot_wavelet(self.data, style, ax=ax1, detail_level = 0)        
        tmp = ax.get_position().bounds
        ax.set_position([tmp[0] , tmp[1], tmp[2]*.9 , tmp[3] ])
        
        ## P-T pdf
        self.plot_PT(scanned=1, ax=ax4)
        
        ## plots best result
        ax, axins, cbar = plot_wavelet( self.corrected_data(self.best_likelyhood[0], self.data, title='best') , style, ax=ax2, detail_level = 0)
        axins.set_ylabel(r'Corrected'+'\n'+'amplitudes')
        tmp = ax.get_position().bounds
        ax.set_position([tmp[0] , tmp[1], tmp[2]*.9 , tmp[3] ])
        
        ## plots best result
        ax, axins, cbar = plot_wavelet( self.corrected_data(self.centroid[0], self.data, title='cent.') , style, ax=ax3, detail_level = 0)
        axins.set_ylabel(r'Corrected'+'\n'+'amplitudes')
        tmp = ax.get_position().bounds
        ax.set_position([tmp[0] , tmp[1], tmp[2]*.9 , tmp[3] ])
        
#         ## plots PT result
#         self.plot_PT(ax=ax3)
    
    def plot_PT(self, scanned=1, data=SyntheticWavelets(mt=None), sol = None, style = '*', ax=None):
        '''
            Plot pdfs
        '''
                
        if self.scanned == 0 or scanned == 0 :
            self.scan(data)
        
        # get pdf #####
        self.PT_pdf() #
        ###############
        if ax == None:
            # create figure, add axes
            ax = (plt.figure(figsize=plt.figaspect(1.))).gca()
     
        # make orthographic basemap.
        map = Basemap(ax=ax, 
                      resolution='c',
                      projection='ortho',
                      lat_0=-90,
                      lon_0=0) 
        
        # define parallels and meridians to draw.
        map.drawparallels(np.arange( -80., 81.,20.), color= '0.75')
        map.drawmeridians(np.arange(-180.,179.,20.), color= '0.75')
   
        
        # Solutions
        sols = [ self.best_likelyhood[0] , self.centroid[0] ]
        markers = ['o' , 'x']
        markeredgewidths = [0, 2]
        
        for i in range(len(sols)):   
                     
            test = MomentTensor(sols[i],system='XYZ',debug=2)
            P = np.asarray(cartesian_to_spherical(test.get_t_axis(system='XYZ')))
            T = np.asarray(cartesian_to_spherical(test.get_p_axis(system='XYZ')))
            
            symetrics = [ 0 , np.pi , -1*np.pi ]
            
            for j,sym in enumerate(symetrics):                
                
                x, y = sphere2basemap(map, P+sym) # map( 180-np.rad2deg(P[0]+sym), -1*(90-np.rad2deg(P[1]+sym)))
                map.plot(x,y,
                         marker=markers[i],
                         color='k', 
                         markeredgewidth=markeredgewidths[i]+2)
                x, y = sphere2basemap(map, T+sym) # map( 180-np.rad2deg(T[0]+sym), -1*(90-np.rad2deg(T[1]+sym)))
                map.plot(x,y,
                         marker=markers[i],
                         color='k', 
                         markeredgewidth=markeredgewidths[i]+2)
                
                x, y = sphere2basemap(map, P+sym) # map( 180-np.rad2deg(P[0]+sym), -1*(90-np.rad2deg(P[1]+sym)))
                map.plot(x,y,
                         marker=markers[i],
                         color='r', 
                         markeredgewidth=markeredgewidths[i])
                x, y = sphere2basemap(map, T+sym) # map( 180-np.rad2deg(T[0]+sym), -1*(90-np.rad2deg(T[1]+sym)))
                map.plot(x,y,
                         marker=markers[i],
                         color='b', 
                         markeredgewidth=markeredgewidths[i])
        
        # Contour maps 
        ## compute native x,y coordinates of grid.
        x, y = sphere2basemap(map, self.pdf['sphere grid']) 
        # x, y = map( 180-np.rad2deg(self.pdf['sphere grid'][0]), -1*(90-np.rad2deg(self.pdf['sphere grid'][1])))
        ## Machinery
        colormaps = [ plt.cm.OrRd , plt.cm.Blues ]
        colorlines = [ 'r' , 'b']
        legends_title = ['P(p-axis|d) [%]', 'P(t-axis|d) [%]']
        inset_locations = [3, 4] 
        locations = ['right', 'left']
        ## 
        for i in range(self.pdf['P/T'].shape[2]):                
            ### set desired contour levels.
            clevs = np.linspace(np.mean(self.pdf['P/T'][:,:,i]),
                                np.max(self.pdf['P/T'][:,:,i]),
                                10) 
            
            ### plot SLP contours.
            CS1 =  map.contour(x,y,self.pdf['P/T'][:,:,i]*100.,clevs*100., 
                             animated=True, colors=colorlines[i], linewidths=0.5)
            CS2 = map.contourf(x,y,self.pdf['P/T'][:,:,i]*100.,clevs*100., 
                             animated=True, cmap=colormaps[i], alpha=.5)
            
            axins = inset_axes(ax,
                   width="10%", # width = 30% of parent_bbox
                   height="10%", 
                   loc=inset_locations[i])
            axins.axis('off')
            
            cbar = map.colorbar(CS2, ax = axins, format="%.0f", location=locations[i])
            cbar.set_label(legends_title[i])
            cbar.ax.yaxis.set_ticks_position(locations[i])
            cbar.ax.yaxis.set_label_position(locations[i])
            tmp = cbar.ax.get_position().bounds
            cbar.ax.set_position([tmp[0] , tmp[1], tmp[2] , tmp[3]*.5 ])
        
        ax.set_title(r'P and T axis (red & blue)'+'\n'+'$^{best \/ and \/ centroid \/( \circ \/&\/ x )}$')
        pos1 = ax.get_position().bounds # get the original position 
        ax.set_position([pos1[0]+pos1[2]*.051 , pos1[1] ,  pos1[2] * .9, pos1[3]]) # set a new position

#         # 3d Plots
#         fig = plt.figure(figsize=plt.figaspect(.5))
#         ax1 = plt.subplot2grid((1,2), (0, 0), projection='3d', aspect='equal', ylim=[-1,1], xlim=[-1,1], zlim=[-1,1], title='P. axis.', xlabel='Lon.', ylabel='Lat.')
#         ax2 = plt.subplot2grid((1,2), (0, 1), projection='3d', aspect='equal', ylim=[-1,1], xlim=[-1,1], zlim=[-1,1], title='T. axis.', xlabel='Lon.', ylabel='Lat.')
#            
#         ## Pressure
#         XYZ = np.asarray(spherical_to_cartesian([np.pi/2. - self.pdf['grid AIR'][0] - np.pi, self.pdf['grid AIR'][1], self.pdf['grid AIR'][2]]))
#         G = np.asarray(spherical_to_cartesian([self.pdf['grid AIR'][0], self.pdf['grid AIR'][1], self.pdf['P/T axis'][:,:,0] ]))
#         plot_seismicsourcemodel(G, XYZ, comp='r', style='x', ax=ax1, cbarxlabel='P-axis likelyhood', alpha=1.)
#     
#         ## Tension
#         G = np.asarray(spherical_to_cartesian([self.pdf['grid AIR'][0], self.pdf['grid AIR'][1], self.pdf['P/T axis'][:,:,1] ]))
#         plot_seismicsourcemodel(G, XYZ, comp='r', style='x', ax=ax2, cbarxlabel='T-axis likelyhood', alpha=1.)
#             

    def demo(self, scanned=0, data=SyntheticWavelets(n=10, mt=None), sol = None):

        data.degrade(snr=[5.,10.], shift = [0.,0.])
        if self.scanned == 0 or scanned == 0 :
            self.scan(data)
        
        if sol == None:
            sol = self.best_likelyhood[0]
        
        
        fig = plt.figure(figsize=plt.figaspect(.85))
        
        # plots the model
        ax = plt.subplot2grid((2,2), (0,0), projection='3d') 
        ax, axins, cbar = plot_wavelet(  self.data , style='s', ax=ax, detail_level = 0)
        fig.delaxes(cbar.ax)
        ax.set_title(r'Synthetic model')
        tmp = ax.get_position().bounds
        ax.set_position([tmp[0] , tmp[1], tmp[2] , tmp[3]*1.2 ])
        
        # plots the best of scan 
        ax = plt.subplot2grid((2,2), (0,1), projection='3d') 
        ax, axins, cbar = plot_wavelet( self.corrected_data(self.best_likelyhood[0], self.data) , style='s', ax=ax, detail_level = 0)           
        fig.delaxes(cbar.ax)
        ax.set_title(r'Best solution')
        axins.set_ylabel(r'Corrected'+'\n'+'amplitudes')  
        tmp = ax.get_position().bounds
        ax.set_position([tmp[0] , tmp[1], tmp[2] , tmp[3]*1.2 ])
        
        # plots some random trials
        changes = np.asarray([90., 180., 270.])
        pos = [[1,0],[1,1],[1,2]] 
        for i,change in enumerate(changes):            
            ## make each trial orientation
            tmp = self.best_likelyhood[0]
            tmp[0] += change 
            if tmp[0] > 360.:
                tmp[0] -= 360.
            
            ## plots each trials
            ax = plt.subplot2grid((2,len(changes)), (1,i), projection='3d')   
            ax, axins, cbar = plot_wavelet( self.corrected_data(tmp, self.data) , style='s', ax=ax, detail_level = 0)        
            fig.delaxes(cbar.ax)            
            ax.set_title(r'Trial '+str(i+1))            
            axins.set_ylabel('')          
            tmp = ax.get_position().bounds
            ax.set_position([tmp[0] , tmp[1], tmp[2]*1.2 , tmp[3] ])
            
            if i==0:
                axins.set_ylabel(r'Corrected'+'\n'+'amplitudes')   
    
    def corrected_data(self, mt, data, title=''):
        
        results = copy.deepcopy(data)
        
        results.SeismicSource = SeismicSource(mt)
        results.MomentTensor = MomentTensor(mt, system='XYZ', debug=2)        
        results.observations['mt'] = mt
        
        amplitudes={}
        source_model = SeismicSource( mt )
        
        ### Loops over wave types ##########
        for wi,w in enumerate(self.waves): #            
            #disp = farfield( np.ravel(results.MomentTensor.get_M())[[0,4,8,1,2,5]] , results.observations['cart'] , w)
            disp, observations_xyz = source_model.Aki_Richards.radpat(wave=w, obs_sph = results.observations['sph'] )        
            #### Loops over components of waves #########
            for ci,c in enumerate(self.components[wi]): #                  
                amplitudes[ w, c ], disp_projected = disp_component(results.observations['cart'], disp, c)
        
        forrms = np.zeros((9999))           
        for i in range(len(results.Stream)):              
            results.Stream[i].data *= np.sign(amplitudes[
                                                         results.observations['types'][i,0], 
                                                         results.Stream[i].stats.channel[-1] ][i])
            
            forrms[:len(results.Stream[i].data)] += results.Stream[i].data * self.data_taperwindows[i]
        
        results.observations['rms'] = np.sum(forrms**2)*np.sign(np.sum(forrms)) 
        
        # get probabilities
        results.observations['P(d|Mt)'] = results.observations['rms']/ self.power_synth_stack
        
        # P to get this Mt overall
        results.observations['P(Mt)'] = np.nanmean(self.source_mechanisms['P(Mt)'])
        
        ## P to get the Mt for the given data
        results.observations['P(Mt|d)'] = results.observations['P(d|Mt)'] * results.observations['P(Mt)'] / self.source_mechanisms['P(d)']
        
        results.title = title+' (P(Mt|d): '+ str(int( 100*results.observations['P(Mt|d)'] )) +'%)'
        
        return results
    
    def PT_pdf(self):
        
        # pdf grid for P-T axis 
        test = np.meshgrid( np.linspace(-np.pi,np.pi,100) , np.linspace(0.,np.pi,50) ) 
        self.pdf = {'sphere grid': (test[0], test[1], np.ones(test[1].shape)), 
                    'P/T': np.zeros([test[1].shape[0], test[1].shape[1], 2])}

        # Machinery  
        mem_clust_coef =  np.zeros([test[1].shape[0], test[1].shape[1], 2])
        spaces = ['P-axis', 'T-axis']
        
        # makes smooth pdf along P-T space # change for sphere distance averaging
        for i,s in enumerate(spaces):     
            
            clust_coef = 1/(haversine( phi1 = self.source_mechanisms[s][:,1],
                                       lon1 = self.source_mechanisms[s][:,0],
                                       phi2 = self.pdf['sphere grid'][1],
                                       lon2 = self.pdf['sphere grid'][0],
                                       radius = 1.) / np.pi )**.5
            
            rms =  np.reshape(self.source_mechanisms['P(Mt|d)']*-1,
                              ( 1, 1, len(self.source_mechanisms['P(Mt|d)'] )))
            
            self.pdf['P/T'][:,:,i] += np.sum( rms * clust_coef , axis=2) 
            mem_clust_coef[:,:,i]  += np.sum( clust_coef , axis=2) 
        
        self.pdf['P/T'] /= mem_clust_coef
        
        self.pdf['P/T'] /= np.max(self.pdf['P/T'])
        self.pdf['P/T'] *= np.max(self.source_mechanisms['P(Mt|d)'])
        
        
    
def mt_diff( mt1, mt2):
    
    fps = np.deg2rad([mt1.get_fps(), mt2.get_fps()])
    diff = [999999999, 999999999]
    for i in range(2):
        for j in range(2):
            
            test = haversine(lon1=fps[0][i][0], phi1=fps[0][i][1], lon2=fps[1][j][0], phi2=fps[1][j][1], radius=1.) 
            
            while test>np.pi/2:
                test -= np.pi/2
                        
            if test < diff[i]:
                diff[i] = test
                    
    return np.rad2deg(np.mean(diff))
        
def test_scan( nstep = 20 , N_tests = [ 16, 32, 64, 128 ], N_bootstrap = 10 , sol='b'):
    
    print 'This may take a long time...'
    
    N_tests = np.asarray(N_tests)
    
    N_range = np.linspace(2,175,nstep)
    gap_range = N_range
    snr_range = np.linspace(.1,10.,nstep)
    shift_range = np.linspace(.0,.5,nstep)
    ndc_range = np.linspace(.01,.99,nstep)
    
    rms = np.zeros([nstep, N_bootstrap, 4, len(N_tests)+1])
    error = np.zeros([nstep, N_bootstrap, 4, len(N_tests)+1])
    labels = []   #np.zeros([4, len(N_tests)])
    labels.append([])
    labels[0].append( r'N, G0$^\circ$' )
    
    c=2  
    simple_models={'LV'   : np.array([c/2,0,0,0.,0.,0.])  ,
                   'Iso.' : np.array([c/2.0001,c/2.000001,c/2.0000000001,0.,0.,0.]) * 1./np.sqrt(3.), 
                   'CLVD' : np.array([-c,c/2,c/2,0.,0.,0.]) * 1./np.sqrt(6.),
                   'DC'   : np.array([0.,0.,0.,np.sqrt(c),0.,0.]) * 1./np.sqrt(2.)  }    
    
    dcscanner = SourceScan()

    for i,N in enumerate(N_range):
        for k in range(N_bootstrap):
            data = SyntheticWavelets(n=int(N), mt=None) 
            dcscanner.scan(data=data)
            if sol is 'c':
                rms[i,k, 0,0] += dcscanner.centroid[1]  #centroid best_likelyhood
                error[i,k, 0,0] +=  mt_diff( MomentTensor(dcscanner.centroid[0]), dcscanner.data.MomentTensor) 
            else:
                rms[i,k, 0,0] += dcscanner.best_likelyhood[1]  #centroid best_likelyhood
                error[i,k, 0,0] +=  mt_diff( MomentTensor(dcscanner.best_likelyhood[0]), dcscanner.data.MomentTensor) 
      
    for j,N in enumerate(N_tests):
        labels.append([])
        labels.append([])
        labels[1].append( 'N'+str(int(N)) )
        labels[2].append( 'N'+str(int(N)) )
        
        if N < N_tests[-1]:
            labels[0].append( 'G, N' + str(int(N)) +'' )
            for i,gap in enumerate(gap_range):                
                for k in range(N_bootstrap):
                    data = SyntheticWavelets(n=int(N), mt=None, gap=gap) 
                    dcscanner.scan(data=data) 
                    if sol is 'c':
                        rms[i,k, 0,j+1] += dcscanner.centroid[1] 
                        error[i,k, 0,j+1] +=  mt_diff( MomentTensor(dcscanner.centroid[0]), dcscanner.data.MomentTensor) 
                    else:
                        rms[i,k, 0,j+1] += dcscanner.best_likelyhood[1] 
                        error[i,k, 0,j+1] +=  mt_diff( MomentTensor(dcscanner.best_likelyhood[0]), dcscanner.data.MomentTensor) 
        
        for i,snr in enumerate(snr_range):                
            for k in range(N_bootstrap):
                data = SyntheticWavelets(n=int(N), mt=None) 
                data.degrade(snr=[snr,snr], shift=[0.,0.])
                dcscanner.scan(data=data) 
                if sol is 'c':
                    rms[i,k, 1,j] += dcscanner.centroid[1] 
                    error[i,k, 1,j] +=  mt_diff( MomentTensor(dcscanner.centroid[0]), dcscanner.data.MomentTensor) 
                else:                    
                    rms[i,k, 1,j] += dcscanner.best_likelyhood[1] 
                    error[i,k, 1,j] +=  mt_diff( MomentTensor(dcscanner.best_likelyhood[0]), dcscanner.data.MomentTensor) 
        
        for i,shift in enumerate(shift_range):       
            for k in range(N_bootstrap):
                data = SyntheticWavelets(n=int(N), mt=None) 
                data.degrade(snr=[10.,10.], shift=[-shift,shift])
                dcscanner.scan(data=data)
                if sol is 'c':
                    rms[i,k, 2,j] += dcscanner.centroid[1] 
                    error[i,k, 2,j] +=  mt_diff( MomentTensor(dcscanner.centroid[0]), dcscanner.data.MomentTensor)  
                else:
                    rms[i,k, 2,j] += dcscanner.best_likelyhood[1] 
                    error[i,k, 2,j] +=  mt_diff( MomentTensor(dcscanner.best_likelyhood[0]), dcscanner.data.MomentTensor)  
                    

    for j,N in enumerate(['LV', 'Iso.', 'CLVD']):  
        labels.append([])
        labels[3].append( N )
        t = [np.round(np.random.uniform(0,2,N_bootstrap)), np.round(np.random.uniform(0,2,N_bootstrap)) ] 
        for i,shift in enumerate(ndc_range):           
            for k in range(N_bootstrap):
                mt = np.asarray([ np.roll((simple_models[N]*shift)[:3], int(t[0][k])), 
                                 np.roll((simple_models['DC']*(1-shift))[3:], int(t[1][k])) ])
                data = SyntheticWavelets(n=300, mt= mt.ravel()) 
                dcscanner.scan(data=data)
                if sol is 'c':
                    rms[i,k, 3,j] += dcscanner.centroid[1] 
                    error[i,k, 3,j] +=  mt_diff( MomentTensor(dcscanner.centroid[0]), dcscanner.data.MomentTensor)  
                else:
                    rms[i,k, 3,j] += dcscanner.best_likelyhood[1] 
                    error[i,k, 3,j] +=  mt_diff( MomentTensor(dcscanner.best_likelyhood[0]), dcscanner.data.MomentTensor)  
                    
    
    rms[np.isnan(rms)] = 0.
    error[np.isnan(error)] = 0.
    
    # Plots
    fig = plt.figure(figsize=(9,9))    
    ax = [plt.subplot2grid((2,2), (0, 0)),
          plt.subplot2grid((2,2), (0, 1)),
          plt.subplot2grid((2,2), (1, 0)),
          plt.subplot2grid((2,2), (1, 1)) ]
    
    colors = ['b', 'g' , 'r', 'c', 'm', 'y', 'k']
    
    x = np.asarray([N_range, snr_range, shift_range, ndc_range])
    for i,name in enumerate(['Test 1: data coverage (N & gap)','Test 2: signal to noise ratio','Test 3: arrival time error', 'Test 4: non-DC component']):    
        for j,N in enumerate(labels[i]):
            ax[i].plot(x[i], np.nanmean(rms[:,:,i,j], axis=1), label=labels[i][j], color=colors[j])
            ax[i].plot(x[i], np.nanmean(error[:,:,i,j]/90, axis=1), '--', color=colors[j])
        
        leg = ax[i].legend(fancybox=True,loc=9, ncol=2,columnspacing=1)
        leg.get_frame().set_alpha(0.5)
        
        ax[i].set_xlabel(name)
        if i == 0 or i == 2:
            ax[i].set_ylabel(r'P(Mt|d) and $\frac{\Delta^\circ}{90}$ (- & --)')
        #ax[i].set_title('Test '+str(i+1) )
        ax[i].grid(True)
        
        ax[i].set_ylim([0., 1.])
            
        

    
         
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





        
