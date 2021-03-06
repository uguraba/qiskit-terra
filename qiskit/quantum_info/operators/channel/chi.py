# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.
"""
Chi-matrix representation of a Quantum Channel.


This is the matrix χ such that:

    E(ρ) = sum_{i, j} χ_{i,j} P_i.ρ.P_j^dagger

where [P_i, i=0,...4^{n-1}] is the n-qubit Pauli basis in lexicographic order.

See [1] for further details.

References:
    [1] C.J. Wood, J.D. Biamonte, D.G. Cory, Quant. Inf. Comp. 15, 0579-0811 (2015)
        Open access: arXiv:1111.6950 [quant-ph]
"""

from numbers import Number

import numpy as np

from qiskit.qiskiterror import QiskitError
from qiskit.quantum_info.operators.channel.quantum_channel import QuantumChannel
from qiskit.quantum_info.operators.channel.choi import Choi
from qiskit.quantum_info.operators.channel.superop import SuperOp
from qiskit.quantum_info.operators.channel.transformations import _to_chi


class Chi(QuantumChannel):
    """Pauli basis Chi-matrix representation of a quantum channel

    The Chi-matrix is the Pauli-basis representation of the Chi-Matrix.
    """

    def __init__(self, data, input_dims=None, output_dims=None):
        """Initialize a Chi quantum channel operator."""
        if isinstance(data, (list, np.ndarray)):
            # Initialize from raw numpy or list matrix.
            chi_mat = np.array(data, dtype=complex)
            # Determine input and output dimensions
            dim_l, dim_r = chi_mat.shape
            if dim_l != dim_r:
                raise QiskitError('Invalid Chi-matrix input.')
            if input_dims:
                input_dim = np.product(input_dims)
            if output_dims:
                output_dim = np.product(input_dims)
            if output_dims is None and input_dims is None:
                output_dim = int(np.sqrt(dim_l))
                input_dim = dim_l // output_dim
            elif input_dims is None:
                input_dim = dim_l // output_dim
            elif output_dims is None:
                output_dim = dim_l // input_dim
            # Check dimensions
            if input_dim * output_dim != dim_l:
                raise QiskitError("Invalid shape for Chi-matrix input.")
        else:
            # Initialize from Qiskit objects
            data = self._init_transformer(data)
            input_dim, output_dim = data.dim
            chi_mat = _to_chi(data.rep, data._data, input_dim, output_dim)
            if input_dims is None:
                input_dims = data.input_dims()
            if output_dims is None:
                output_dims = data.output_dims()
        # Check input is N-qubit channel
        nqubits = int(np.log2(input_dim))
        if 2**nqubits != input_dim:
            raise QiskitError("Input is not an n-qubit Chi matrix.")
        # Check and format input and output dimensions
        input_dims = self._automatic_dims(input_dims, input_dim)
        output_dims = self._automatic_dims(output_dims, output_dim)
        super().__init__('Chi', chi_mat, input_dims, output_dims)

    @property
    def _bipartite_shape(self):
        """Return the shape for bipartite matrix"""
        return (self._input_dim, self._output_dim, self._input_dim,
                self._output_dim)

    def conjugate(self):
        """Return the conjugate of the QuantumChannel."""
        # Since conjugation is basis dependent we transform
        # to the Choi representation to compute the
        # conjugate channel
        return Chi(Choi(self).conjugate())

    def transpose(self):
        """Return the transpose of the QuantumChannel."""
        # Since conjugation is basis dependent we transform
        # to the Choi representation to compute the
        # conjugate channel
        return Chi(Choi(self).transpose())

    def compose(self, other, qubits=None, front=False):
        """Return the composition channel self∘other.

        Args:
            other (QuantumChannel): a quantum channel.
            qubits (list): a list of subsystem positions to compose other on.
            front (bool): If False compose in standard order other(self(input))
                          otherwise compose in reverse order self(other(input))
                          [default: False]

        Returns:
            Chi: The composition channel as a Chi object.

        Raises:
            QiskitError: if other is not a QuantumChannel subclass, or
            has incompatible dimensions.
        """
        if qubits is not None:
            # TODO
            raise QiskitError("NOT IMPLEMENTED: subsystem composition.")

        # Convert other to Choi since we convert via Choi
        if not isinstance(other, Choi):
            other = Choi(other)
        # Check dimensions match up
        if front and self._input_dim != other._output_dim:
            raise QiskitError(
                'input_dim of self must match output_dim of other')
        if not front and self._output_dim != other._input_dim:
            raise QiskitError(
                'input_dim of other must match output_dim of self')
        # Since we cannot directly add two channels in the Chi
        # representation we convert to the Choi representation
        return Chi(Choi(self).compose(other, front=front))

    def power(self, n):
        """The matrix power of the channel.

        Args:
            n (int): compute the matrix power of the superoperator matrix.

        Returns:
            Chi: the matrix power of the SuperOp converted to a Chi channel.

        Raises:
            QiskitError: if the input and output dimensions of the
            QuantumChannel are not equal, or the power is not an integer.
        """
        if n > 0:
            return super().power(n)
        return Chi(SuperOp(self).power(n))

    def tensor(self, other):
        """Return the tensor product channel self ⊗ other.

        Args:
            other (QuantumChannel): a quantum channel.

        Returns:
            Chi: the tensor product channel self ⊗ other as a Chi object.

        Raises:
            QiskitError: if other is not a QuantumChannel subclass.
        """
        return self._tensor_product(other, reverse=False)

    def expand(self, other):
        """Return the tensor product channel other ⊗ self.

        Args:
            other (QuantumChannel): a quantum channel.

        Returns:
            Chi: the tensor product channel other ⊗ self as a Chi object.

        Raises:
            QiskitError: if other is not a QuantumChannel subclass.
        """
        return self._tensor_product(other, reverse=True)

    def add(self, other):
        """Return the QuantumChannel self + other.

        Args:
            other (QuantumChannel): a quantum channel.

        Returns:
            Chi: the linear addition self + other as a Chi object.

        Raises:
            QiskitError: if other is not a QuantumChannel subclass, or
            has incompatible dimensions.
        """
        if not isinstance(other, Chi):
            other = Chi(other)
        if self.dim != other.dim:
            raise QiskitError("other QuantumChannel dimensions are not equal")
        return Chi(self._data + other.data, self._input_dims,
                   self._output_dims)

    def subtract(self, other):
        """Return the QuantumChannel self - other.

        Args:
            other (QuantumChannel): a quantum channel.

        Returns:
            Chi: the linear subtraction self - other as Chi object.

        Raises:
            QiskitError: if other is not a QuantumChannel subclass, or
            has incompatible dimensions.
        """
        if not isinstance(other, Chi):
            other = Chi(other)
        if self.dim != other.dim:
            raise QiskitError("other QuantumChannel dimensions are not equal")
        return Chi(self._data - other.data, self._input_dims,
                   self._output_dims)

    def multiply(self, other):
        """Return the QuantumChannel self + other.

        Args:
            other (complex): a complex number.

        Returns:
            Chi: the scalar multiplication other * self as a Chi object.

        Raises:
            QiskitError: if other is not a valid scalar.
        """
        if not isinstance(other, Number):
            raise QiskitError("other is not a number")
        return Chi(other * self._data, self._input_dims, self._output_dims)

    def _evolve(self, state, qubits=None):
        """Evolve a quantum state by the QuantumChannel.

        Args:
            state (QuantumState): The input statevector or density matrix.
            qubits (list): a list of QuantumState subsystem positions to apply
                           the operator on.

        Returns:
            DensityMatrix: the output quantum state as a density matrix.
        """
        return Choi(self)._evolve(state, qubits)

    def _tensor_product(self, other, reverse=False):
        """Return the tensor product channel.

        Args:
            other (QuantumChannel): a quantum channel.
            reverse (bool): If False return self ⊗ other, if True return
                            if True return (other ⊗ self) [Default: False
        Returns:
            Chi: the tensor product channel as a Chi object.

        Raises:
            QiskitError: if other is not a QuantumChannel subclass.
        """
        if not isinstance(other, Chi):
            other = Chi(other)
        if reverse:
            input_dims = self.input_dims() + other.input_dims()
            output_dims = self.output_dims() + other.output_dims()
            data = np.kron(other.data, self._data)
        else:
            input_dims = other.input_dims() + self.input_dims()
            output_dims = other.output_dims() + self.output_dims()
            data = np.kron(self._data, other.data)
        return Chi(data, input_dims, output_dims)
