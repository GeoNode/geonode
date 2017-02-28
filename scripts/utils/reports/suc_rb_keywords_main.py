#!/usr/bin/env python
from suc_rb_keywords import caller_function
import argparse

def parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'type', choices=['sar', 'dem', 'fhm', 'all'], action='append')
    parser.add_argument('-l','--layer',action='append')
    args = parser.parse_args()
    print args
    print args.layer
    return args

args = parse_arguments()
# exit(1)
for argType in args.type:
    if argType == 'sar':
        # SAR DEM
        # pl1 suc muni
        print '#' * 40
        print 'SAR DEM'
        keyword_filter = 'sar'
        caller_function(keyword_filter,args.layer)
        print 'FINISHED SAR DEM'
        print '#' * 40
    elif argType == 'dem':
        # DEM COVERAGE
        # dream rb
        print '#' * 40
        print 'DEM'
        keyword_filter = 'dem'
        caller_function(keyword_filter,args.layer)
        print 'FINISHED DEM COVERAGE'
        print '#' * 40
    elif argType == 'fhm':
        # FHM
        # fhm coverage
        print '#' * 40
        print 'FLOOD HAZARD MAPS'
        keyword_filter = 'fhm'
        caller_function(keyword_filter,args.layer)
        print 'FINISHED FLOOD HAZARD MAPS'
        print '#' * 40
    elif argType == 'all':
        print '#' * 40
        print 'TAGGING FHMs, DEM Coverages, SAR DEMs'
        keyword_filters = ['fhm','dem','sar']
        for k in keyword_filters:
            print ' TAGGING ' + k.upper()
            caller_function(k,args.layer)
            print 'FINISHED ' + k.upper()
        print '#' * 40
    # elif arg == 'coverage':
    #     # COVERAGE
    #     # parse in name
    #     print '#' * 40
    #     print 'COVERAGES'
    #     keyword_filter = 'coverage'
    #     caller_function(keyword_filter)
    #     print 'FINISHED COVERAGES'
    #     print '#' * 40
