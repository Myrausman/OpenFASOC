# change to ext/ directory because the extract command generates .ext files
# in the current directory
cd $OBJECTS_DIR/netgen_lvs/ext/

# generate lvs netlist using magic
cat > magic.script <<EOF
gds flatglob *\$\$*
gds read $1
load $2

if {![string compare $2 "ldoInst"]} {
  select top cell
  flatten ldoInst_flat
  load ldoInst_flat
  cellname delete ldoInst
  cellname rename ldoInst_flat ldoInst
  select top cell
} else {
    select top cell
}
extract all
ext2spice lvs
ext2spice -o ../spice/$2_lvsmag.spice
load $2
extract all
ext2spice lvs
ext2spice rthresh 0
ext2spice cthresh 0
ext2spice -o ../spice/$2_pex.spice
load $2
extract all
ext2spice cthresh 0
ext2spice -o ../spice/$2_sim.spice
exit
EOF

magic -rcfile $COMMON_VERIF_DIR/sky130A/sky130A.magicrc -noconsole -dnull < magic.script

# Adapt the extracted spice file to account for errors in Magic
# Importantly, this script is specific in what it looks for,
# so is unlikely to break LVS if Magic improves in the future
# note that --toplevel is optional (specify if you have a top level subckt)
# note also that you must have the global variable "__open_generator_name__" specified to your generator (as described in the python script)
python3 $COMMON_VERIF_DIR/process_extracted_pins.py --lvsmag $OBJECTS_DIR/netgen_lvs/spice/$2_lvsmag.spice --toplevel $2 --generator $__open_generator_name__

# run lvs check using netgen
# netgen lvs $2_lvsmag.spice $2.spice $COMMON_VERIF_DIR/sky130A/sky130A_setup.tcl $3 -full
# Run netgen in batch mode
netgen -batch lvs "$OBJECTS_DIR/netgen_lvs/spice/$2_lvsmag.spice $2" "$OBJECTS_DIR/netgen_lvs/spice/$2.spice $2" $COMMON_VERIF_DIR/sky130A/sky130A_setup.tcl $3
