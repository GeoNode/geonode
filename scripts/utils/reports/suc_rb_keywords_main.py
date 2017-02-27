#!/usr/bin/env python
from suc_rb_keywords import caller_function
import argparse


def parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'type', choices=['sar', 'dem', 'fhm'], action='append')
    args = parser.parse_args()
    return args

args = parse_arguments()
for arg in args.type:
    if arg == 'sar':
        # SAR DEM
        # pl1 suc muni
        print '#' * 40
        print 'SAR DEM'
        keyword_filter = 'sar'
        caller_function(keyword_filter)
        print 'FINISHED SAR DEM'
        print '#' * 40
    elif arg == 'dem':
        # DEM COVERAGE
        # dream rb
        print '#' * 40
        print 'DEM'
        keyword_filter = 'dem'
        caller_function(keyword_filter)
        print 'FINISHED DEM COVERAGE'
        print '#' * 40
    elif arg == 'fhm':
        # FHM
        # fhm coverage
        print '#' * 40
        print 'FLOOD HAZARD MAPS'
        keyword_filter = 'fhm'
        caller_function(keyword_filter)
        print 'FINISHED FLOOD HAZARD MAPS'
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
