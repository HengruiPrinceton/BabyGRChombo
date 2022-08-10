# myinitialconditions.py

# set the initial conditions for all the variables

from myparams import *
from source.uservariables import *
from source.tensoralgebra import *
from source.fourthorderderivatives import *
import numpy as np
from scipy.interpolate import interp1d

def get_initial_vars_values() :

    initial_vars_values = np.zeros(NUM_VARS * N)

    # Use oscilloton data to construct functions for the vars
    grr0_data    = np.loadtxt("source/initial_data/grr0.csv")
    lapse0_data  = np.loadtxt("source/initial_data/lapse0.csv")
    v0_data      = np.loadtxt("source/initial_data/v0.csv")
    
    # set up grid in radial direction in areal polar coordinates
    dR = 0.01
    length = np.size(grr0_data)
    R = np.linspace(0, dR*(length-1), num=length)
    f_grr   = interp1d(R, grr0_data)
    f_lapse = interp1d(R, lapse0_data)
    f_v     = interp1d(R, v0_data)
    
    for ix in range(num_ghosts, N-num_ghosts) :

        # position on the grid
        r_i = r[ix]

        # scalar field values
        initial_vars_values[ix + idx_u * N] = 0.0 # start at a moment where field is zero
        initial_vars_values[ix + idx_v * N] = f_v(r_i)
 
        # non zero metric variables (note h_rr etc are rescaled difference from flat space so zero
        # and conformal factor is zero for flat space)
        initial_vars_values[ix + idx_lapse * N] = f_lapse(r_i)
        # note that we choose that the determinant \bar{gamma} = \hat{gamma} initially
        grr_here = f_grr(r_i)
        phys_gamma_over_r4sin2theta = grr_here
        phi_here = - 1.0/12.0 * np.log(phys_gamma_over_r4sin2theta)
        initial_vars_values[ix + idx_phi * N]   = phi_here
        em4phi = np.exp(-4.0*phi_here)
        initial_vars_values[ix + idx_hrr * N]   = em4phi * grr_here - 1
        initial_vars_values[ix + idx_htt * N]   = em4phi - 1
        initial_vars_values[ix + idx_hpp * N]   = em4phi - 1
        
    # overwrite outer boundaries with extrapolation (zeroth order)
    for ivar in range(0, NUM_VARS) :
        boundary_cells = np.array([(ivar + 1)*N-3, (ivar + 1)*N-2, (ivar + 1)*N-1])
        for count, ix in enumerate(boundary_cells) :
            offset = -1 - count
            initial_vars_values[ix]    = initial_vars_values[ix + offset]

    # overwrite inner cells using parity under r -> - r
    for ivar in range(0, NUM_VARS) :
        boundary_cells = np.array([(ivar)*N, (ivar)*N+1, (ivar)*N+2])
        var_parity = parity[ivar]
        for count, ix in enumerate(boundary_cells) :
            offset = 5 - 2*count
            initial_vars_values[ix] = initial_vars_values[ix + offset] * var_parity           

    # needed for lambdar
    hrr    = initial_vars_values[idx_hrr * N : (idx_hrr + 1) * N]
    htt    = initial_vars_values[idx_htt * N : (idx_htt + 1) * N]
    hpp    = initial_vars_values[idx_hpp * N : (idx_hpp + 1) * N]
    dhrrdx     = get_dfdx(hrr)
    dhttdx     = get_dfdx(htt)
    dhppdx     = get_dfdx(hpp)
    
    # assign lambdar values
    for ix in range(num_ghosts, N-num_ghosts) :

        # position on the grid
        r_here = r[ix]
        
        # Assign BSSN vars to local tensors
        h = np.zeros_like(rank_2_spatial_tensor)
        h[i_r][i_r] = hrr[ix]
        h[i_t][i_t] = htt[ix]
        h[i_p][i_p] = hpp[ix]
        
        dhdr = np.zeros_like(rank_2_spatial_tensor)
        dhdr[i_r][i_r] = dhrrdx[ix]
        dhdr[i_t][i_t] = dhttdx[ix]
        dhdr[i_p][i_p] = dhppdx[ix]
        
        # (unscaled) \bar\gamma_ij and \bar\gamma^ij
        bar_gamma_LL = get_metric(r_here, h)
        bar_gamma_UU = get_inverse_metric(r_here, h)
        
        # The connections Delta^i, Delta^i_jk and Delta_ijk
        Delta_U, Delta_ULL, Delta_LLL  = get_connection(r_here, bar_gamma_UU, bar_gamma_LL, h, dhdr)
        initial_vars_values[ix + idx_lambdar * N]   = Delta_U[i_r]

    # Fill boundary cells for lambdar
    boundary_cells = np.array([(idx_lambdar + 1)*N-3, (idx_lambdar + 1)*N-2, (idx_lambdar + 1)*N-1])
    for count, ix in enumerate(boundary_cells) :
        offset = -1 - count
        initial_vars_values[ix]    = initial_vars_values[ix + offset]
        
    boundary_cells = np.array([(idx_lambdar)*N, (idx_lambdar)*N+1, (idx_lambdar)*N+2])
    for count, ix in enumerate(boundary_cells) :
        offset = 5 - 2*count
        initial_vars_values[ix] = initial_vars_values[ix + offset] * parity[idx_lambdar]
        
    return initial_vars_values
