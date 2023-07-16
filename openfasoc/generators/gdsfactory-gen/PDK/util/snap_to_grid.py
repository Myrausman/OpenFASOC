from gdsfactory.typings import Component
from pydantic import validate_arguments
from typing import Optional, Union, Iterable, Literal
from gdsfactory.pdk import get_grid_size
from tempfile import TemporaryDirectory
from pathlib import Path
from gdsfactory.read.import_gds import import_gds
from decimal import Decimal
from gdsfactory.snap import snap_to_grid


@validate_arguments
def component_snap_to_grid(comp: Component, nm: Optional[int]=None) -> Component:
	"""snaps all polygons in component to grid and correctly updates ports
	comp = the component to snap to grid
	NOTE this function will flatten the component
	nm the grid to snap to, defaults to active pdk grid size"""
	# flatten the component
	comp = comp.flatten()
	# figure out nm
	if nm is None:
		nm = int(get_grid_size() * 1000)
	elif nm == 0:
		return comp
	elif nm < 0:
		raise ValueError("nm must be an integer tolerance value greater than zero")
	# iterate through ports and snap to grid
	comp.snap_ports_to_grid(nm=nm)
	save_ports = comp.get_ports_list()
	save_name = comp.name
	with TemporaryDirectory() as tmpdirname:
		tmp_gds_path = Path(comp.write_gds(gdsdir=tmpdirname)).resolve()
		comp = import_gds(gdspath=tmp_gds_path).copy()
	comp.add_ports(save_ports)
	comp.name = save_name
	return comp


@validate_arguments
def snap_to_2xgrid(dims: Union[list[Union[float,Decimal]], Union[float,Decimal]], return_type: Literal["decimal","float","same"]="same") -> Union[list[Union[float,Decimal]], Union[float,Decimal]]:
	"""snap all numbers in dims to double the grid size.
	This is useful when a generator accepts a size or dimension argument
	because there is a chance the cell may be centered (resulting in off grid components)
	args:
	dims = a list OR single number specifying the dimensions to snap to grid
	return_type = return a decimal, float, or the same type that was passed to the function
	"""
	dims = dims if isinstance(dims, Iterable) else [dims]
	dimtype_in = None
	nm = 2 * 1000 * int(get_grid_size())
	# snap dims to grid
	snapped_dims = list()
	for dim in dims:
		dimtype_in = type(dim)
		snapped_dims.append(snap_to_grid(float(dim), nm=nm))
	# convert to correct type
	if return_type=="decimal" or (return_type=="same" and dimtype_in==Decimal):
		for i, snapped_dim in enumerate(snapped_dims):
			snapped_dims[i] = Decimal(str(snapped_dim))
	# correctly return list or single element
	return snapped_dims[0] if len(snapped_dims)==1 else snapped_dims
