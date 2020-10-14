import numpy as np
import scipy.sparse as sp
from discretize.utils.code_utils import is_scalar, deprecate_function
import warnings


def mkvc(x, n_dims=1, **kwargs):
    """Creates a vector with specified dimensionality.

    This function converts numpy.ndarray to a vector. In general,
    the output vector has a dimension of 1. However, the dimensionality
    can be specified if the user intends to carry out a dot product with
    a higher order array.

    Parameters
    ----------
    x: numpy.ndarray
        An nD array that will be reorganized and output as a vector
    n_dims: int
        The dimension of the output vector.

    Returns
    -------
    numpy.ndarray
        The output vector

    Examples
    --------

    Here, we reorganize a simple 2D array as a vector and demonstrate the
    impact of the *n_dim* argument.

    >>> from discretize.utils import mkvc
    >>> import numpy as np
    >>> 
    >>> a = np.random.rand(3, 2)
    >>> print('Original array:\n', a)
    >>> 
    >>> v = mkvc(a)
    >>> print('\nVector with n_dim = 1:\n', v, '\n')
    >>> 
    >>> for ii in range(1, 4):
    >>>     temp = mkvc(a, ii)
    >>>     print('Shape of output with n_dim =', ii, ': ', np.shape(temp))


    """
    if "numDims" in kwargs:
        warnings.warn(
            "The numDims keyword argument has been deprecated, please use n_dims. "
            "This will be removed in discretize 1.0.0",
            FutureWarning,
        )
        n_dims = kwargs["numDims"]
    if type(x) == np.matrix:
        x = np.array(x)

    if hasattr(x, "tovec"):
        x = x.tovec()

    if isinstance(x, Zero):
        return x

    if not isinstance(x, np.ndarray):
        raise TypeError("Vector must be a numpy array")

    if n_dims == 1:
        return x.flatten(order="F")
    elif n_dims == 2:
        return x.flatten(order="F")[:, np.newaxis]
    elif n_dims == 3:
        return x.flatten(order="F")[:, np.newaxis, np.newaxis]


def sdiag(h):
    """Generate sparse diagonal matrix from vector containing diagonal elements"""
    if isinstance(h, Zero):
        return Zero()

    return sp.spdiags(mkvc(h), 0, h.size, h.size, format="csr")


def sdinv(M):
    """Return inverse of a sparse diagonal matrix"""
    return sdiag(1.0 / M.diagonal())


def speye(n):
    """Generate sparse identity matrix"""
    return sp.identity(n, format="csr")


def kron3(A, B, C):
    """Three kron prods"""
    return sp.kron(sp.kron(A, B), C, format="csr")


def spzeros(n1, n2):
    """Generate sparse matrix of zeros"""
    return sp.dia_matrix((n1, n2))


def ddx(n):
    """Define 1D derivatives, inner, this means we go from n+1 to n"""
    return sp.spdiags((np.ones((n + 1, 1)) * [-1, 1]).T, [0, 1], n, n + 1, format="csr")


def av(n):
    """Define 1D averaging operator from nodes to cell-centers."""
    return sp.spdiags(
        (0.5 * np.ones((n + 1, 1)) * [1, 1]).T, [0, 1], n, n + 1, format="csr"
    )


def av_extrap(n):
    """Define 1D averaging operator from cell-centers to nodes."""
    Av = sp.spdiags(
        (0.5 * np.ones((n, 1)) * [1, 1]).T, [-1, 0], n + 1, n, format="csr"
    ) + sp.csr_matrix(([0.5, 0.5], ([0, n], [0, n - 1])), shape=(n + 1, n))
    return Av


def ndgrid(*args, **kwargs):
    """Generate gridded locations for 1D, 2D, or 3D tensors.

    For 1D, 2D, or 3D tensors, this function takes the unique positions defining
    a tensor along each of its axis and returns the gridded locations.
    For 2D and 3D meshes, the user may treat the unique *x*, *y* (and *z*)
    positions a successive positional arguments or as a single argument using
    a list [*x*, *y*, (*z*)].

    For outputs, let *dim* be the number of dimension (1, 2 or 3) and let *n* be
    the total number of gridded locations. The gridded *x*, *y* (and *z*) locations
    can be return as a single numpy array of shape [n, ndim]. The user can also
    return the gridded *x*, *y* (and *z*) locations as a list of length *ndim*.
    The list contains entries contain the *x*, *y* (and *z*) locations as tensors.
    See examples.

    Parameters
    ----------
    args: numpy.ndarray or a list of numpy.ndarray
        Positions along each axis of the tensor. The user can define these as
        successive positional arguments *x*, *y*, (and *z*) or as a single argument
        using a list [*x*, *y*, (*z*)].
    vector: Bool, optional kwarg
        If *True*, the output is a numpy array of dimension [n, ndim]. If *False*,
        the gridded x, y (and z) locations are returned as separate ndarrays in a list.
        Default is *True*.
    order: String, optional kwarg
        Define ordering using one of the following options {'C', 'F', 'A'}.
        'C' is C-like ordering. 'F' is Fortran-like ordering. 'A' is Fortran
        ordering if memory is contigious and C-like otherwise. Default = 'F'.
        See numpy.reshape for more on this argument.
    
    Returns
    -------
    numpy.ndarray or list of numpy.array
        If *vector=True* the gridded *x*, *y*, (and *z*) locations are
        returned as a numpy array of shape [n, ndim]. If *vector=False*,
        the gridded *x*, *y*, (and *z*) are returned as a list of vectors.
    
    Examples
    --------
    Here we generate a 2D grid and return it as a single numpy array.
    
    >>> from discretize.utils import *
    >>> import numpy as np
    >>> 
    >>> x = np.array([1, 2, 3])
    >>> y = np.array([2, 4])
    >>> 
    >>> xy = ndgrid([x, y])
    >>> print('Gridded x,y locations with F ordering:\n', xy)
    >>> 
    >>> xy = ndgrid([x, y], order='C')
    >>> print('\nGridded x,y locations with C ordering:\n', xy)
    >>> 
    >>> xy = ndgrid(x, y, vector=False)
    >>> print('\nX location tensor:\n', xy[0])
    >>> print('\nY location tensor:\n', xy[1])

    """

    # Read the keyword arguments, and only accept a vector=True/False
    vector = kwargs.pop("vector", True)
    order = kwargs.pop("order", "F")
    if not isinstance(vector, bool):
        raise TypeError("'vector' keyword must be a bool")

    # you can either pass a list [x1, x2, x3] or each seperately
    if type(args[0]) == list:
        xin = args[0]
    else:
        xin = args

    # Each vector needs to be a numpy array
    try:
        if len(xin) == 1:
            return np.array(xin[0])
        meshed = np.meshgrid(*xin, indexing="ij")
    except Exception:
        raise TypeError("All arguments must be array like")

    if vector:
        return np.column_stack([x.reshape(-1, order=order) for x in meshed])
    return meshed


def ind2sub(shape, inds):
    """From the given shape, returns the subscripts of the given index"""
    if type(inds) is not np.ndarray:
        inds = np.array(inds)
    if len(inds.shape) != 1:
        raise ValueError("Indexing must be done as a 1D row vector, e.g. [3,6,6,...]")
    return np.unravel_index(inds, shape, order="F")


def sub2ind(shape, subs):
    """From the given shape, returns the index of the given subscript"""
    if len(shape) == 1:
        return subs
    if type(subs) is not np.ndarray:
        subs = np.array(subs)
    if len(subs.shape) == 1:
        subs = subs[np.newaxis, :]
    if subs.shape[1] != len(shape):
        raise ValueError(
            "Indexing must be done as a column vectors. e.g. [[3,6],[6,2],...]"
        )
    inds = np.ravel_multi_index(subs.T, shape, order="F")
    return mkvc(inds)


def get_subarray(A, ind):
    """subarray"""
    if not isinstance(ind, list):
        raise TypeError("ind must be a list of vectors")
    if len(A.shape) != len(ind):
        raise ValueError("ind must have the same length as the dimension of A")

    if len(A.shape) == 2:
        return A[ind[0], :][:, ind[1]]
    elif len(A.shape) == 3:
        return A[ind[0], :, :][:, ind[1], :][:, :, ind[2]]
    else:
        raise Exception("get_subarray does not support dimension asked.")


def inverse_3x3_block_diagonal(
    a11, a12, a13, a21, a22, a23, a31, a32, a33, return_matrix=True, **kwargs
):
    """B = inverse_3x3_block_diagonal(a11, a12, a13, a21, a22, a23, a31, a32, a33)

    inverts a stack of 3x3 matrices

    Input:
     A   - a11, a12, a13, a21, a22, a23, a31, a32, a33

    Output:
     B   - inverse
    """
    if "returnMatrix" in kwargs:
        warnings.warn(
            "The returnMatrix keyword argument has been deprecated, please use return_matrix. "
            "This will be removed in discretize 1.0.0",
            FutureWarning,
        )
        return_matrix = kwargs["returnMatrix"]

    a11 = mkvc(a11)
    a12 = mkvc(a12)
    a13 = mkvc(a13)
    a21 = mkvc(a21)
    a22 = mkvc(a22)
    a23 = mkvc(a23)
    a31 = mkvc(a31)
    a32 = mkvc(a32)
    a33 = mkvc(a33)

    detA = (
        a31 * a12 * a23
        - a31 * a13 * a22
        - a21 * a12 * a33
        + a21 * a13 * a32
        + a11 * a22 * a33
        - a11 * a23 * a32
    )

    b11 = +(a22 * a33 - a23 * a32) / detA
    b12 = -(a12 * a33 - a13 * a32) / detA
    b13 = +(a12 * a23 - a13 * a22) / detA

    b21 = +(a31 * a23 - a21 * a33) / detA
    b22 = -(a31 * a13 - a11 * a33) / detA
    b23 = +(a21 * a13 - a11 * a23) / detA

    b31 = -(a31 * a22 - a21 * a32) / detA
    b32 = +(a31 * a12 - a11 * a32) / detA
    b33 = -(a21 * a12 - a11 * a22) / detA

    if not return_matrix:
        return b11, b12, b13, b21, b22, b23, b31, b32, b33

    return sp.vstack(
        (
            sp.hstack((sdiag(b11), sdiag(b12), sdiag(b13))),
            sp.hstack((sdiag(b21), sdiag(b22), sdiag(b23))),
            sp.hstack((sdiag(b31), sdiag(b32), sdiag(b33))),
        )
    )


def inverse_2x2_block_diagonal(a11, a12, a21, a22, return_matrix=True, **kwargs):
    """B = inverse_2x2_block_diagonal(a11, a12, a21, a22)

    Inverts a stack of 2x2 matrices by using the inversion formula

    inv(A) = (1/det(A)) * cof(A)^T

    Input:
    A   - a11, a12, a21, a22

    Output:
    B   - inverse
    """
    if "returnMatrix" in kwargs:
        warnings.warn(
            "The returnMatrix keyword argument has been deprecated, please use return_matrix. "
            "This will be removed in discretize 1.0.0",
            FutureWarning,
        )
        return_matrix = kwargs["returnMatrix"]

    a11 = mkvc(a11)
    a12 = mkvc(a12)
    a21 = mkvc(a21)
    a22 = mkvc(a22)

    # compute inverse of the determinant.
    detAinv = 1.0 / (a11 * a22 - a21 * a12)

    b11 = +detAinv * a22
    b12 = -detAinv * a12
    b21 = -detAinv * a21
    b22 = +detAinv * a11

    if not return_matrix:
        return b11, b12, b21, b22

    return sp.vstack(
        (sp.hstack((sdiag(b11), sdiag(b12))), sp.hstack((sdiag(b21), sdiag(b22))))
    )


class TensorType(object):
    def __init__(self, M, tensor):
        if tensor is None:  # default is ones
            self._tt = -1
            self._tts = "none"
        elif is_scalar(tensor):
            self._tt = 0
            self._tts = "scalar"
        elif tensor.size == M.nC:
            self._tt = 1
            self._tts = "isotropic"
        elif (M.dim == 2 and tensor.size == M.nC * 2) or (
            M.dim == 3 and tensor.size == M.nC * 3
        ):
            self._tt = 2
            self._tts = "anisotropic"
        elif (M.dim == 2 and tensor.size == M.nC * 3) or (
            M.dim == 3 and tensor.size == M.nC * 6
        ):
            self._tt = 3
            self._tts = "tensor"
        else:
            raise Exception("Unexpected shape of tensor: {}".format(tensor.shape))

    def __str__(self):
        return "TensorType[{0:d}]: {1!s}".format(self._tt, self._tts)

    def __eq__(self, v):
        return self._tt == v

    def __le__(self, v):
        return self._tt <= v

    def __ge__(self, v):
        return self._tt >= v

    def __lt__(self, v):
        return self._tt < v

    def __gt__(self, v):
        return self._tt > v


def make_property_tensor(M, tensor):
    if tensor is None:  # default is ones
        tensor = np.ones(M.nC)

    if is_scalar(tensor):
        tensor = tensor * np.ones(M.nC)

    propType = TensorType(M, tensor)
    if propType == 1:  # Isotropic!
        Sigma = sp.kron(sp.identity(M.dim), sdiag(mkvc(tensor)))
    elif propType == 2:  # Diagonal tensor
        Sigma = sdiag(mkvc(tensor))
    elif M.dim == 2 and tensor.size == M.nC * 3:  # Fully anisotropic, 2D
        tensor = tensor.reshape((M.nC, 3), order="F")
        row1 = sp.hstack((sdiag(tensor[:, 0]), sdiag(tensor[:, 2])))
        row2 = sp.hstack((sdiag(tensor[:, 2]), sdiag(tensor[:, 1])))
        Sigma = sp.vstack((row1, row2))
    elif M.dim == 3 and tensor.size == M.nC * 6:  # Fully anisotropic, 3D
        tensor = tensor.reshape((M.nC, 6), order="F")
        row1 = sp.hstack(
            (sdiag(tensor[:, 0]), sdiag(tensor[:, 3]), sdiag(tensor[:, 4]))
        )
        row2 = sp.hstack(
            (sdiag(tensor[:, 3]), sdiag(tensor[:, 1]), sdiag(tensor[:, 5]))
        )
        row3 = sp.hstack(
            (sdiag(tensor[:, 4]), sdiag(tensor[:, 5]), sdiag(tensor[:, 2]))
        )
        Sigma = sp.vstack((row1, row2, row3))
    else:
        raise Exception("Unexpected shape of tensor")

    return Sigma


def inverse_property_tensor(M, tensor, return_matrix=False, **kwargs):
    if "returnMatrix" in kwargs:
        warnings.warn(
            "The returnMatrix keyword argument has been deprecated, please use return_matrix. "
            "This will be removed in discretize 1.0.0",
            FutureWarning,
        )
        return_matrix = kwargs["returnMatrix"]

    propType = TensorType(M, tensor)

    if is_scalar(tensor):
        T = 1.0 / tensor
    elif propType < 3:  # Isotropic or Diagonal
        T = 1.0 / mkvc(tensor)  # ensure it is a vector.
    elif M.dim == 2 and tensor.size == M.nC * 3:  # Fully anisotropic, 2D
        tensor = tensor.reshape((M.nC, 3), order="F")
        B = inverse_2x2_block_diagonal(
            tensor[:, 0], tensor[:, 2], tensor[:, 2], tensor[:, 1], return_matrix=False
        )
        b11, b12, b21, b22 = B
        T = np.r_[b11, b22, b12]
    elif M.dim == 3 and tensor.size == M.nC * 6:  # Fully anisotropic, 3D
        tensor = tensor.reshape((M.nC, 6), order="F")
        B = inverse_3x3_block_diagonal(
            tensor[:, 0],
            tensor[:, 3],
            tensor[:, 4],
            tensor[:, 3],
            tensor[:, 1],
            tensor[:, 5],
            tensor[:, 4],
            tensor[:, 5],
            tensor[:, 2],
            return_matrix=False,
        )
        b11, b12, b13, b21, b22, b23, b31, b32, b33 = B
        T = np.r_[b11, b22, b33, b12, b13, b23]
    else:
        raise Exception("Unexpected shape of tensor")

    if return_matrix:
        return make_property_tensor(M, T)

    return T


class Zero(object):

    __numpy_ufunc__ = True
    __array_ufunc__ = None

    def __add__(self, v):
        return v

    def __radd__(self, v):
        return v

    def __iadd__(self, v):
        return v

    def __sub__(self, v):
        return -v

    def __rsub__(self, v):
        return v

    def __isub__(self, v):
        return v

    def __mul__(self, v):
        return self

    def __rmul__(self, v):
        return self

    def __div__(self, v):
        return self

    def __truediv__(self, v):
        return self

    def __rdiv__(self, v):
        raise ZeroDivisionError("Cannot divide by zero.")

    def __rtruediv__(self, v):
        raise ZeroDivisionError("Cannot divide by zero.")

    def __rfloordiv__(self, v):
        raise ZeroDivisionError("Cannot divide by zero.")

    def __pos__(self):
        return self

    def __neg__(self):
        return self

    def __lt__(self, v):
        return 0 < v

    def __le__(self, v):
        return 0 <= v

    def __eq__(self, v):
        return v == 0

    def __ne__(self, v):
        return not (0 == v)

    def __ge__(self, v):
        return 0 >= v

    def __gt__(self, v):
        return 0 > v

    def transpose(self):
        return self

    @property
    def T(self):
        return self


class Identity(object):

    __numpy_ufunc__ = True
    __array_ufunc__ = None

    _positive = True

    def __init__(self, positive=True):
        self._positive = positive

    def __pos__(self):
        return self

    def __neg__(self):
        return Identity(not self._positive)

    def __add__(self, v):
        if sp.issparse(v):
            return v + speye(v.shape[0]) if self._positive else v - speye(v.shape[0])
        return v + 1 if self._positive else v - 1

    def __radd__(self, v):
        return self.__add__(v)

    def __sub__(self, v):
        return self + -v

    def __rsub__(self, v):
        return -self + v

    def __mul__(self, v):
        return v if self._positive else -v

    def __rmul__(self, v):
        return v if self._positive else -v

    def __div__(self, v):
        if sp.issparse(v):
            raise NotImplementedError("Sparse arrays not divisibile.")
        return 1 / v if self._positive else -1 / v

    def __truediv__(self, v):
        if sp.issparse(v):
            raise NotImplementedError("Sparse arrays not divisibile.")
        return 1.0 / v if self._positive else -1.0 / v

    def __rdiv__(self, v):
        return v if self._positive else -v

    def __rtruediv__(self, v):
        return v if self._positive else -v

    def __floordiv__(self, v):
        return 1 // v if self._positive else -1 // v

    def __rfloordiv__(self, v):
        return 1 // v if self._positivie else -1 // v

    def __lt__(self, v):
        return 1 < v if self._positive else -1 < v

    def __le__(self, v):
        return 1 <= v if self._positive else -1 <= v

    def __eq__(self, v):
        return v == 1 if self._positive else v == -1

    def __ne__(self, v):
        return (not (1 == v)) if self._positive else (not (-1 == v))

    def __ge__(self, v):
        return 1 >= v if self._positive else -1 >= v

    def __gt__(self, v):
        return 1 > v if self._positive else -1 > v

    @property
    def T(self):
        return self

    def transpose(self):
        return self


sdInv = deprecate_function(sdinv, "sdInv", removal_version="1.0.0")
getSubArray = deprecate_function(get_subarray, "getSubArray", removal_version="1.0.0")
inv3X3BlockDiagonal = deprecate_function(
    inverse_3x3_block_diagonal, "inv3X3BlockDiagonal", removal_version="1.0.0"
)
inv2X2BlockDiagonal = deprecate_function(
    inverse_2x2_block_diagonal, "inv2X2BlockDiagonal", removal_version="1.0.0"
)
makePropertyTensor = deprecate_function(
    make_property_tensor, "makePropertyTensor", removal_version="1.0.0"
)
invPropertyTensor = deprecate_function(
    inverse_property_tensor, "invPropertyTensor", removal_version="1.0.0"
)
