'''
Extract metrics table.
'''

from __future__ import division
from collections import OrderedDict

import argparse
import os
import pandas as pd

#=======================================================================================================================
# Read Command Line Input
#=======================================================================================================================
parser = argparse.ArgumentParser()

parser.add_argument('metrics_dir',
                    help='''Path to metrics directory generated by alignment pipeline.''')

parser.add_argument('out_file',
                    help='''Path to .csv file where table output will be written.''')

parser.add_argument('--library_id',
                    help='''Optional identifier string for the library.''')


parser.add_argument('--samplesheet',
                    help='''Optional identifier string for the library.''')
args = parser.parse_args()

#=======================================================================================================================
# Functions
#=======================================================================================================================

def parse_samplesheet(sample_sheet):
    """
    get info
    """
    sample_info = open(sample_sheet)

    metrics = pd.DataFrame()

    header = True
    for line in sample_info:
        line = line.strip().split(',')

        if header and line[0] == "[Data]":
            header = False
        elif header:
            continue
        else:
            if line[0] in ['Sample_ID', 'Sample-ID']:
                assert line[1:] == ['Sample_Name','Sample_Plate','Sample_Well',
                                    'I7_Index_ID', 'index','I5_Index_ID','index2',
                                    'Sample_Project','Description']
                continue

            sample_id = line[0]
            plate = line[2]
            well = line[3]
            i5 = line[4]
            i7 = line[6]
    
            samp_desc = line[9]
            samp_desc = samp_desc.split(';')
            samp_desc = [v.split('=') for v in samp_desc]
            cell_call= [v[1] for v in samp_desc if v[0]=='CC'][0]
            exp_cond= [v[1] for v in samp_desc if v[0]=='EC'][0]
    
            well = well if well != '' else 'R1_C1'
            plate = plate if plate !='' else 'R1-C1'
            i5 = i5 if i5!='' else 'i5-1'
            i7 = i7  if i7 != '' else 'i7-1'
    
            sample_metrics = pd.DataFrame(OrderedDict([
    					       ('sample_id', [sample_id]),
    					       ('cell_call', [cell_call]),
                                               ('experimental_condition', [exp_cond]),
                                               ('sample_well', [well]),
                                               ('sample_plate', [plate]),
                                               ('i5_index', [i5]),
                                               ('i7_index', [i7]),
    					       ]))
    
            metrics = metrics.append(sample_metrics)
    
    metrics = metrics.reset_index(drop=True)
    
    return metrics


def _extract_wgs_metrics(metrics_file):
    """
    get the coverage_depth (mean_coverage column)
    get the coverage_breadth (count/genome_territory)
    """

    mfile = open(metrics_file)
    
    metrics = []
    hist = {}
    
    addmetrics = False
    addhist = False
   
   
    for line in mfile:
        if line.strip() == '':
            continue
        if line.startswith('## METRICS CLASS'):
            addmetrics = True
            addhist = False
            continue

        if line.startswith('## HISTOGRAM'):
            addhist = True
            addmetrics = False
            continue
        
        if addmetrics:
            metrics.append(line.strip().split('\t'))
        if addhist:
            line = line.strip().split('\t')
            if line[0] == 'coverage':
                continue
            hist[int(line[0])] = int(line[1])

    mfile.close()
    header, data = metrics

    header = [v.lower() for v in header]
    header = {v:i for i,v in enumerate(header)}

    gen_territory = int(data[header['genome_territory']])
    cov_depth  = float(data[header['mean_coverage']])
    count = int(hist[0])
    cov_breadth = (gen_territory - count) / gen_territory 

    return cov_breadth, cov_depth




def extract_wgs_metrics(dir):
    ''' Extract coverage depth and breadth '''
    
    metrics = pd.DataFrame()
    
    for file in os.listdir(dir):
        if file.endswith('.txt'):
            sample_id = file.split('.')[0]

            cov_breadth, cov_depth = _extract_wgs_metrics(os.path.join(dir, file))
            
#            df = pd.read_table(os.path.join(dir, file), sep='\t', header=6, skipfooter=1, engine='python')
#            
#            df_metrics = df.iloc[[0]]
#            df_metrics.columns = [x.lower() for x in df_metrics.columns]
#            
#            df_hist = df.iloc[4:,0:2]
#            df_hist.columns = ['coverage', 'count']
#            df_hist = df_hist.reset_index(drop=True)
#            print os.path.join(dir, file)
#            print df_metrics 
#            genome_territory = int(df_metrics.ix[0, 'genome_territory'])
#            
#            coverage_depth = df_metrics.ix[0, 'mean_coverage']
#            coverage_breadth = (genome_territory - int(df_hist.ix[0, 'count'])) / genome_territory
            
            sample_metrics = pd.DataFrame(OrderedDict([
                                                       ('sample_id', [sample_id]), 
                                                       ('coverage_depth', [cov_depth]), 
                                                       ('coverage_breadth', [cov_breadth])
                                                       ]))
            
            metrics = metrics.append(sample_metrics)
    
    metrics = metrics.reset_index(drop=True)
    
    return metrics


def _extract_insert_metrics(metrics_file):
    ''' Extract median and mean insert size '''

    # picardtools insertmetrics completes with code 0 and doesn't generate metrics file
    # if inputs don't have sufficient read count
    if not os.path.isfile(metrics_file):
        return 0, 0, 0

    mfile = open(metrics_file)
    
    targetlines = []
    
    line = mfile.readline()
    
    while line != '':
        if line.startswith('## METRICS CLASS'):
            targetlines.append(mfile.readline().strip().split('\t'))
            targetlines.append(mfile.readline().strip().split('\t'))
            break
        line = mfile.readline()

    mfile.close()

    header, data = targetlines

    header = [v.lower() for v in header]
    header = {v:i for i,v in enumerate(header)}

    median_ins_size = data[header['median_insert_size']]
    mean_ins_size = data[header['mean_insert_size']]
    std_dev_ins_size = data[header['standard_deviation']]

    return median_ins_size, mean_ins_size, std_dev_ins_size


def extract_insert_metrics(dir):
    ''' Extract median and mean insert size '''
    
    metrics = pd.DataFrame()
    
    for file in os.listdir(dir):
        if file.endswith('.txt'):
            sample_id = file.split('.')[0]
     
            median_ins_size, mean_ins_size, std_dev_ins_size = _extract_insert_metrics(os.path.join(dir, file))
       
#            df = pd.read_table(os.path.join(dir, file), sep='\t', header=6, skipfooter=1, engine='python')
#            
#            df_metrics = df.iloc[[0]]
#            df_metrics.columns = [x.lower() for x in df_metrics.columns]
#            
#            df_hist = df.iloc[4:,0:2]
#            df_hist.columns = ['size', 'count']
#            df_hist = df_hist.reset_index(drop=True)
#            
            sample_metrics = pd.DataFrame(OrderedDict([
                                                       ('sample_id', [sample_id]), 
                                                       ('median_insert_size', median_ins_size), 
                                                       ('mean_insert_size', mean_ins_size),
                                                       ('standard_deviation_insert_size', std_dev_ins_size)
                                                       ]))
            
            metrics = metrics.append(sample_metrics)
    
    metrics = metrics.reset_index(drop=True)
        
    return metrics


def _extract_duplication_metrics(metrics_file):
    """
    extract from markdups
    """

    mfile = open(metrics_file)

    targetlines = []

    line = mfile.readline()

    while line != '':
        if line.startswith('## METRICS CLASS'):
            targetlines.append(mfile.readline().strip('\n').split('\t'))
            targetlines.append(mfile.readline().strip('\n').split('\t'))
            break
        line = mfile.readline()

    mfile.close()

    header, data = targetlines

    header = [v.lower() for v in header]
    header = {v:i for i,v in enumerate(header)}

    unprd_mpd_rds = int(data[header['unpaired_reads_examined']])
    prd_mpd_rds = int(data[header['read_pairs_examined']])
    unprd_dup_rds = int(data[header['unpaired_read_duplicates']])
    prd_dup_rds = int(data[header['read_pair_duplicates']])
    unmpd_rds = data[header['unmapped_reads']]
    est_lib_size = data[header['estimated_library_size']]

    rd_pair_opt_dup = int(data[header['read_pair_optical_duplicates']])

    try:
        perc_dup_reads = (unprd_dup_rds + ((prd_dup_rds + rd_pair_opt_dup) * 2)) / (unprd_mpd_rds + (prd_mpd_rds * 2))
    except ZeroDivisionError:
        perc_dup_reads = 0

    outdata = (unprd_mpd_rds, prd_mpd_rds, unprd_dup_rds, prd_dup_rds,
               unmpd_rds, perc_dup_reads, est_lib_size)

    outdata = tuple(['nan' if val == '' else val for val in outdata])
    return outdata

def extract_duplication_metrics(dir):
    ''' Extract duplication metrics and library size '''
    
    metrics = pd.DataFrame()
    for file in os.listdir(dir):
        if file.endswith('.txt'):
            sample_id = file.split('.')[0]
            

            (unprd_mpd_rds, prd_mpd_rds, unprd_dup_rds, prd_dup_rds,
               unmpd_rds, perc_dup_reads, est_lib_size) = _extract_duplication_metrics(os.path.join(dir, file))

#            df = pd.read_table(os.path.join(dir, file), sep='\t', header=6, skipfooter=1, engine='python')
#            
#            df.columns = [x.lower() for x in df.columns]
#
#            if any(df['library'] == '## HISTOGRAM'):
#                hist_index = df['library'][df['library'] == '## HISTOGRAM'].index.tolist()[0]
#                
#                df_metrics = df[0:hist_index-1]
#            else: 
#                df_metrics = df[0:-1]
#           
#            if len(df) > 1:
#                df_metrics = df_metrics.drop(['library', 'percent_duplication'], axis=1).sum(axis=0)
#                
#                df_metrics['percent_duplication'] = (df_metrics['unpaired_read_duplicates'] + 
#                                                   ((df_metrics['read_pair_duplicates'] + df_metrics['read_pair_optical_duplicates']) * 2)) / \
#                                                    (df_metrics['unpaired_reads_examined'] + (df_metrics['read_pairs_examined'] * 2))
#                
#                df_metrics = pd.DataFrame(df_metrics).transpose()
#            
            sample_metrics = pd.DataFrame(OrderedDict([
                                                       ('sample_id', [sample_id]), 
                                                       ('unpaired_mapped_reads', [unprd_mpd_rds]), 
                                                       ('paired_mapped_reads', [prd_mpd_rds]), 
                                                       ('unpaired_duplicate_reads', [unprd_dup_rds]), 
                                                       ('paired_duplicate_reads', [prd_dup_rds]), 
                                                       ('unmapped_reads', [unmpd_rds]), 
                                                       ('percent_duplicate_reads', [perc_dup_reads]), 
                                                       ('estimated_library_size', [est_lib_size]), 
                                                       ]))
            
            metrics = metrics.append(sample_metrics)
    
    metrics = metrics.reset_index(drop=True)
    
    return metrics

def extract_flagstat_metrics(dir):
    ''' Extract basic flagstat metrics '''
    
    metrics = pd.DataFrame()
    
    for file in os.listdir(dir):
        if file.endswith('.txt'):
            sample_id = file.split('.')[0]
            
            df = pd.read_table(os.path.join(dir, file), sep=r'\s\+\s0\s', header=None, names=['value', 'type'], engine='python')
            
            sample_metrics = pd.DataFrame(OrderedDict([
                                                       ('sample_id', [sample_id]), 
                                                       ('total_reads', [df.ix[0, 'value']]), 
                                                       ('total_mapped_reads', [df.ix[2, 'value']]), 
                                                       ('total_duplicate_reads', [df.ix[1, 'value']]), 
                                                       ('total_properly_paired', [df.ix[6, 'value']])
                                                       ]))
            
            metrics = metrics.append(sample_metrics)
    
    metrics = metrics.reset_index(drop=True)
    
    return metrics

#=======================================================================================================================
# Run script
#=======================================================================================================================

'''
NOTE: 
- All duplicate reads are mapped, since the duplicate flagging is done based on mapping coordinates!

args.library_id = 'PX0218'
args.metrics_dir = '/share/lustre/asteif/projects/single_cell_indexing/alignment/PX0218/9_cycles/metrics'
args.out_file = '/share/lustre/asteif/projects/single_cell_indexing/test/PX0218.metrics_table.csv'

args.metrics_dir = '/share/scratch/asteif_temp/single_cell_indexing/merge/test_gatk_realign/metrics'
args.out_file = '/share/scratch/asteif_temp/single_cell_indexing/merge/test_gatk_realign/metrics/summary/test_gatk_realign.metrics_table.csv'

'''

def main():
    duplication_metrics_dir = os.path.join(args.metrics_dir, 'duplication_metrics')
    flagstat_metrics_dir = os.path.join(args.metrics_dir, 'flagstat_metrics')
    insert_metrics_dir = os.path.join(args.metrics_dir, 'insert_metrics')
    wgs_metrics_dir = os.path.join(args.metrics_dir, 'wgs_metrics')
    
    duplication_metrics = extract_duplication_metrics(duplication_metrics_dir)
    flagstat_metrics = extract_flagstat_metrics(flagstat_metrics_dir)
    wgs_metrics = extract_wgs_metrics(wgs_metrics_dir)
    
    metrics_table = flagstat_metrics.merge(
                    duplication_metrics, on='sample_id').merge(
                    wgs_metrics, on='sample_id')
    
    # runs with single-end reads will not have insert metrics
    if len(os.listdir(insert_metrics_dir)) > 0:
        insert_metrics = extract_insert_metrics(insert_metrics_dir)
        
        metrics_table = metrics_table.merge(insert_metrics, on='sample_id')
    
    if args.library_id:
        metrics_table.insert(0,'library_id', args.library_id)

    if args.samplesheet:
        sampmet = parse_samplesheet(args.samplesheet)
        metrics_table = metrics_table.merge(sampmet, on='sample_id')
    
    metrics_table.to_csv(args.out_file, index=False)

if __name__ == '__main__':
    main()
