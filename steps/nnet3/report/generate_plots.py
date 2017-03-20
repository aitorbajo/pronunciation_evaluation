#!/usr/bin/env python


# Copyright 2016 Vijayaditya Peddinti.
# Apache 2.0.

import warnings
import imp
import argparse
import os
import errno
import logging
import re
import subprocess
train_lib = imp.load_source('ntl', 'steps/nnet3/nnet3_train_lib.py')

try:
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import numpy as np

    plot = True
except ImportError:
    warnings.warn("""
This script requires matplotlib and numpy. Please install them to generate plots. Proceeding with generation of tables.
If you are on a cluster where you do not have admin rights you could try using virtualenv.""")
    plot = False

nlp = imp.load_source('nlp', 'steps/nnet3/report/nnet3_log_parse_lib.py')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(filename)s:%(lineno)s - %(funcName)s - %(levelname)s ] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info('Generating plots')


def GetArgs():
    parser = argparse.ArgumentParser(description="""
Parses the training logs and generates a variety of plots.
example : steps/nnet3/report/generate_plots.py --comparison-dir exp/nnet3/tdnn1 --comparison-dir exp/nnet3/tdnn2 exp/nnet3/tdnn exp/nnet3/tdnn/report
""")
    parser.add_argument("--comparison-dir", type=str, action='append', help="other experiment directories for comparison. These will only be used for plots, not tables")
    parser.add_argument("--start-iter", type=int, help="Iteration from which plotting will start", default = 1)
    parser.add_argument("--is-chain", type=str, default = False, action = train_lib.StrToBoolAction, help="Iteration from which plotting will start")
    parser.add_argument("exp_dir", help="experiment directory, e.g. exp/nnet3/tdnn")
    parser.add_argument("output_dir", help="experiment directory, e.g. exp/nnet3/tdnn/report")

    args = parser.parse_args()
    if args.comparison_dir is not None and len(args.comparison_dir) > 6:
        raise Exception("max 6 --comparison-dir options can be specified. If you want to compare with more comparison_dir, you would have to carefully tune the plot_colors variable which specified colors used for plotting.")
    assert(args.start_iter >= 1)
    return args

plot_colors = ['red', 'blue', 'green', 'black', 'magenta', 'yellow', 'cyan' ]



class LatexReport:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file
        self.document=[]
        self.document.append("""
\documentclass[prl,10pt,twocolumn]{revtex4}
\usepackage{graphicx}    % Used to import the graphics
\\begin{document}
""")

    def AddFigure(self, figure_pdf, title):
        # we will have keep extending this replacement list based on errors during compilation
        # escaping underscores in the title
        title = "\\texttt{"+re.sub("_","\_", title)+"}"
        fig_latex = """
%...
\\newpage
\\begin{figure}[h]
  \\begin{center}
    \caption{""" + title + """}
    \includegraphics[width=\\textwidth]{""" + figure_pdf + """}
  \end{center}
\end{figure}
\clearpage
%...
"""
        self.document.append(fig_latex)

    def Close(self):
        self.document.append("\end{document}")
        return self.Compile()

    def Compile(self):
        root, ext = os.path.splitext(self.pdf_file)
        dir_name = os.path.dirname(self.pdf_file)
        latex_file = root + ".tex"
        lat_file = open(latex_file, "w")
        lat_file.write("\n".join(self.document))
        lat_file.close()
        logger.info("Compiling the latex report.")
        try:
            proc = subprocess.Popen(['pdflatex', '-interaction=batchmode', '-output-directory='+str(dir_name), latex_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.communicate()
        except Exception as e:
            logger.warning("There was an error compiling the latex file {0}, please do it manually.".format(latex_file))
            return False
        return True

def LatexCompliantName(name_string):
    # this function is required as latex does not allow all the component names
    # allowed by nnet3.
    # Identified incompatibilities :
    #   1. latex does not allow dot(.) in file names
    #
    node_name_string = re.sub("\.", "_dot_", name_string)

    return node_name_string

def GenerateAccuracyPlots(exp_dir, output_dir, plot, key = 'accuracy', file_basename = 'accuracy', comparison_dir = None, start_iter = 1, latex_report = None):
    assert(start_iter >= 1)

    if plot:
        fig = plt.figure()
        plots = []

    comparison_dir = [] if comparison_dir is None else comparison_dir
    dirs = [exp_dir] + comparison_dir
    index = 0
    for dir in dirs:
        [accuracy_report, accuracy_times, accuracy_data] = nlp.GenerateAccuracyReport(dir, key)
        if index == 0:
            # this is the main experiment directory
            acc_file = open("{0}/{1}.log".format(output_dir, file_basename), "w")
            acc_file.write(accuracy_report)
            acc_file.close()

        if plot:
            color_val = plot_colors[index]
            data = np.array(accuracy_data)
            if data.shape[0] == 0:
                raise Exception("Couldn't find any rows for the accuracy plot")
            data = data[data[:,0]>=start_iter, :]
            plot_handle, = plt.plot(data[:, 0], data[:, 1], color = color_val, linestyle = "--", label = "train {0}".format(dir))
            plots.append(plot_handle)
            plot_handle, = plt.plot(data[:, 0], data[:, 2], color = color_val, label = "valid {0}".format(dir))
            plots.append(plot_handle)
        index += 1
    if plot:
        plt.xlabel('Iteration')
        plt.ylabel(key)
        lgd = plt.legend(handles=plots, loc='lower center', bbox_to_anchor=(0.5, -0.2 + len(dirs) * -0.1 ), ncol=1, borderaxespad=0.)
        plt.grid(True)
        fig.suptitle("{0} plot".format(key))
        figfile_name = '{0}/{1}.pdf'.format(output_dir, file_basename)
        plt.savefig(figfile_name, bbox_extra_artists=(lgd,), bbox_inches='tight')
        if latex_report is not None:
            latex_report.AddFigure(figfile_name, "Plot of {0} vs iterations".format(key))

def GenerateNonlinStatsPlots(exp_dir, output_dir, plot, comparison_dir = None, start_iter = 1, latex_report = None):
    assert(start_iter >= 1)

    comparison_dir = [] if comparison_dir is None else comparison_dir
    dirs = [exp_dir] + comparison_dir
    index = 0
    stats_per_dir = {}

    for dir in dirs:
        stats_per_component_per_iter = nlp.ParseProgressLogsForNonlinearityStats(dir)
        stats_per_dir[dir] = stats_per_component_per_iter

    # convert the nonlin stats into tables
    stat_tables_per_component_per_dir = {}
    for dir in dirs:
        stats_per_component_per_iter = stats_per_dir[dir]
        component_names = stats_per_component_per_iter.keys()
        stat_tables_per_component = {}
        for component_name in component_names:
            comp_data = stats_per_component_per_iter[component_name]
            comp_type = comp_data['type']
            comp_stats = comp_data['stats']
            iters = comp_stats.keys()
            iters.sort()
            iter_stats = []
            for iter in iters:
                iter_stats.append([iter] + comp_stats[iter])
            stat_tables_per_component[component_name] = iter_stats
        stat_tables_per_component_per_dir[dir] = stat_tables_per_component

    main_stat_tables = stat_tables_per_component_per_dir[exp_dir]
    for component_name in main_stat_tables.keys():
        # this is the main experiment directory
        file = open("{dir}/nonlinstats_{comp_name}.log".format(dir = output_dir, comp_name = component_name), "w")
        file.write("Iteration\tValueMean\tValueStddev\tDerivMean\tDerivStddev\n")
        iter_stat_report = ""
        iter_stats = main_stat_tables[component_name]
        for row in iter_stats:
            iter_stat_report += "\t".join(map(lambda x: str(x), row)) + "\n"
        file.write(iter_stat_report)
        file.close()

    if plot:
        main_component_names = main_stat_tables.keys()
        main_component_names.sort()

        plot_component_names = set(main_component_names)
        for dir in dirs:
            component_names = set(stats_per_dir[dir].keys())
            plot_component_names = plot_component_names.intersection(component_names)
        plot_component_names = list(plot_component_names)
        plot_component_names.sort()
        if plot_component_names != main_component_names:
            logger.warning("The components in all the neural networks in the given experiment dirs are not the same, so comparison plots are provided only for common component names. Make sure that these are comparable experiments before analyzing these plots.")

        fig = plt.figure()
        for component_name in main_component_names:
            fig.clf()
            index = 0
            plots = []
            for dir in dirs:
                color_val = plot_colors[index]
                index += 1
                try:
                    iter_stats = stat_tables_per_component_per_dir[dir][component_name]
                except KeyError:
                    # this component is not available in this network so lets not just plot it
                    continue

                data = np.array(iter_stats)
                data = data[data[:,0] >=start_iter, :]
                ax = plt.subplot(211)
                mp, = ax.plot(data[:,0], data[:,1], color=color_val, label="Mean {0}".format(dir))
                msph, = ax.plot(data[:,0], data[:,1] + data[:,2], color=color_val, linestyle='--', label = "Mean+-Stddev {0}".format(dir))
                mspl, = ax.plot(data[:,0], data[:,1] - data[:,2], color=color_val, linestyle='--')
                plots.append(mp)
                plots.append(msph)
                ax.set_ylabel('Value-{0}'.format(comp_type))
                ax.grid(True)

                ax = plt.subplot(212)
                mp, = ax.plot(data[:,0], data[:,3], color=color_val)
                msph, = ax.plot(data[:,0], data[:,3] + data[:,4], color=color_val, linestyle='--')
                mspl, = ax.plot(data[:,0], data[:,3] - data[:,4], color=color_val, linestyle='--')
                ax.set_xlabel('Iteration')
                ax.set_ylabel('Derivative-{0}'.format(comp_type))
                ax.grid(True)

            lgd = plt.legend(handles=plots, loc='lower center', bbox_to_anchor=(0.5, -0.5 + len(dirs) * -0.2 ), ncol=1, borderaxespad=0.)
            plt.grid(True)
            fig.suptitle("Mean and stddev of the value and derivative at {comp_name}".format(comp_name = component_name))
            comp_name = LatexCompliantName(component_name)
            figfile_name = '{dir}/nonlinstats_{comp_name}.pdf'.format(dir = output_dir, comp_name = comp_name)
            fig.savefig(figfile_name, bbox_extra_artists=(lgd,), bbox_inches='tight')
            if latex_report is not None:
                latex_report.AddFigure(figfile_name, "Mean and stddev of the value and derivative at {0}".format(component_name))

def GenerateClippedProportionPlots(exp_dir, output_dir, plot, comparison_dir = None, start_iter = 1, latex_report = None):
    assert(start_iter >= 1)

    comparison_dir = [] if comparison_dir is None else comparison_dir
    dirs = [exp_dir] + comparison_dir
    index = 0
    stats_per_dir = {}
    for dir in dirs:
        try:
            stats_per_dir[dir] = nlp.ParseProgressLogsForClippedProportion(dir)
        except nlp.MalformedClippedProportionLineException as e:
            raise e
        except train_lib.KaldiCommandException as e:
            warnings.warn("Could not extract the clipped proportions for {0},"
                          " this might be because there are no "
                          "ClipGradientComponents.".format(dir))
            continue
    try:
        main_cp_stats = stats_per_dir[exp_dir]['table']
    except KeyError:
        warnings.warn("The main experiment directory {0} does not have clipped"
                      " proportions. So not generating clipped proportion plots.".format(exp_dir))
        return

    # this is the main experiment directory
    file = open("{dir}/clipped_proportion.log".format(dir = output_dir), "w")
    iter_stat_report = ""
    for row in main_cp_stats:
        iter_stat_report += "\t".join(map(lambda x: str(x), row)) + "\n"
    file.write(iter_stat_report)
    file.close()

    if plot:
        main_component_names = stats_per_dir[exp_dir]['cp_per_iter_per_component'].keys()
        main_component_names.sort()
        plot_component_names = set(main_component_names)
        for dir in dirs:
            try:
                component_names = set(stats_per_dir[dir]['cp_per_iter_per_component'].keys())
                plot_component_names = plot_component_names.intersection(component_names)
            except KeyError:
                continue
        plot_component_names = list(plot_component_names)
        plot_component_names.sort()
        if plot_component_names != main_component_names:
            logger.warning("The components in all the neural networks in the given experiment dirs are not the same, so comparison plots are provided only for common component names. Make sure that these are comparable experiments before analyzing these plots.")

        fig = plt.figure()
        for component_name in main_component_names:
            fig.clf()
            index = 0
            plots = []
            for dir in dirs:
                color_val = plot_colors[index]
                index += 1
                try:
                    iter_stats = stats_per_dir[dir]['cp_per_iter_per_component'][component_name]
                except KeyError:
                    # this component is not available in this network so lets not just plot it
                    continue

                data = np.array(iter_stats)
                data = data[data[:,0] >=start_iter, :]
                ax = plt.subplot(111)
                mp, = ax.plot(data[:,0], data[:,1], color=color_val, label="Clipped Proportion {0}".format(dir))
                plots.append(mp)
                ax.set_ylabel('Clipped Proportion')
                ax.set_ylim([0, 1.2])
                ax.grid(True)
            lgd = plt.legend(handles=plots, loc='lower center', bbox_to_anchor=(0.5, -0.5 + len(dirs) * -0.2 ), ncol=1, borderaxespad=0.)
            plt.grid(True)
            fig.suptitle("Clipped-proportion value at {comp_name}".format(comp_name = component_name))
            comp_name = LatexCompliantName(component_name)
            figfile_name = '{dir}/clipped_proportion_{comp_name}.pdf'.format(dir = output_dir, comp_name = comp_name)
            fig.savefig(figfile_name, bbox_extra_artists=(lgd,), bbox_inches='tight')
            if latex_report is not None:
                latex_report.AddFigure(figfile_name, "Clipped proportion at {0}".format(component_name))

def GenerateParameterDiffPlots(exp_dir, output_dir, plot, comparison_dir = None, start_iter = 1, latex_report = None):
    # Parameter changes
    assert(start_iter >= 1)

    comparison_dir = [] if comparison_dir is None else comparison_dir
    dirs = [exp_dir] + comparison_dir
    index = 0
    stats_per_dir = {}
    key_file = {"Parameter differences" : "parameter.diff",
                "Relative parameter differences" : "relative_parameter.diff"}
    stats_per_dir = {}
    for dir in dirs:
        stats_per_dir[dir] = {}
        for key in key_file.keys():
            stats_per_dir[dir][key] = nlp.ParseProgressLogsForParamDiff(dir, key, logger)

    # write down the stats for the main experiment directory
    for diff_type in key_file.keys():
        file = open("{0}/{1}".format(output_dir, key_file[diff_type]), "w")
        diff_per_component_per_iter = stats_per_dir[exp_dir][diff_type]['progress_per_component']
        component_names = stats_per_dir[exp_dir][diff_type]['component_names']
        max_iter = stats_per_dir[exp_dir][diff_type]['max_iter']
        file.write(" ".join(["Iteration"] + component_names)+"\n")
        total_missing_iterations = 0
        gave_user_warning = False
        for iter in range(max_iter + 1):
            iter_data = [str(iter)]
            for c in component_names:
                try:
                    iter_data.append(str(diff_per_component_per_iter[c][iter]))
                except KeyError:
                    total_missing_iterations += 1
                    iter_data.append("NA")
            if (total_missing_iterations/len(component_names) > 20) and not gave_user_warning :
                logger.warning("There are more than {0} missing iterations per component. Something might be wrong.".format(total_missing_iterations/len(component_names)))
                gave_user_warning = True

            file.write(" ".join(iter_data)+"\n")
        file.close()

    if plot:
        # get the component names
        diff_type = key_file.keys()[0]
        main_component_names = stats_per_dir[exp_dir][diff_type]['progress_per_component'].keys()
        main_component_names.sort()
        plot_component_names = set(main_component_names)

        for dir in dirs:
            try:
                component_names = set(stats_per_dir[dir][diff_type]['progress_per_component'].keys())
                plot_component_names = plot_component_names.intersection(component_names)
            except KeyError:
                continue
        plot_component_names = list(plot_component_names)
        plot_component_names.sort()
        if plot_component_names != main_component_names:
            logger.warning("The components in all the neural networks in the given experiment dirs are not the same, so comparison plots are provided only for common component names. Make sure that these are comparable experiments before analyzing these plots.")

        assert(main_component_names)

        fig = plt.figure()
        logger.info("Generating parameter-difference plots for the following components:{0}".format(', '.join(main_component_names)))


        for component_name in main_component_names:
            fig.clf()
            index = 0
            plots = []
            for dir in dirs:
                color_val = plot_colors[index]
                index += 1
                iter_stats = []
                try:
                    for diff_type in ['Parameter differences', 'Relative parameter differences']:
                        iter_stats.append(np.array(sorted(stats_per_dir[dir][diff_type]['progress_per_component'][component_name].items())))
                except KeyError as e:
                    # this component is not available in this network so lets not just plot it
                    if dir==exp_dir:
                        raise Exception("No parameter differences were available even in the main experiment dir for the component {0}. Something went wrong.".format(component_name))
                    continue
                ax = plt.subplot(211)
                mp, = ax.plot(iter_stats[0][:,0], iter_stats[0][:,1], color=color_val, label="Parameter Differences {0}".format(dir))
                plots.append(mp)
                ax.set_ylabel('Parameter Differences')
                ax.grid(True)

                ax = plt.subplot(212)
                mp, = ax.plot(iter_stats[1][:,0], iter_stats[1][:,1], color=color_val, label="Relative Parameter Differences {0}".format(dir))
                ax.set_xlabel('Iteration')
                ax.set_ylabel('Relative Parameter Differences')
                ax.grid(True)

            lgd = plt.legend(handles=plots, loc='lower center', bbox_to_anchor=(0.5, -0.5 + len(dirs) * -0.2 ), ncol=1, borderaxespad=0.)
            plt.grid(True)
            fig.suptitle("Parameter differences at {comp_name}".format(comp_name = component_name))
            comp_name = LatexCompliantName(component_name)
            figfile_name = '{dir}/param_diff_{comp_name}.pdf'.format(dir = output_dir, comp_name = comp_name)
            fig.savefig(figfile_name, bbox_extra_artists=(lgd,), bbox_inches='tight')
            if latex_report is not None:
                latex_report.AddFigure(figfile_name, "Parameter differences at {0}".format(component_name))

def GeneratePlots(exp_dir, output_dir, comparison_dir = None, start_iter = 1, is_chain = False):
    try:
        os.makedirs(output_dir)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(output_dir):
            pass
        else:
            raise e
    if plot:
        latex_report = LatexReport("{0}/report.pdf".format(output_dir))
    else:
        latex_report = None

    if is_chain:
        logger.info("Generating log-probability plots")
        GenerateAccuracyPlots(exp_dir, output_dir, plot, key = 'log-probability', file_basename = 'log_probability', comparison_dir = comparison_dir, start_iter = start_iter, latex_report = latex_report)
    else:
        logger.info("Generating accuracy plots")
        GenerateAccuracyPlots(exp_dir, output_dir, plot, key = 'accuracy', file_basename = 'accuracy', comparison_dir = comparison_dir, start_iter = start_iter, latex_report = latex_report)

        logger.info("Generating log-likelihood plots")
        GenerateAccuracyPlots(exp_dir, output_dir, plot, key = 'log-likelihood', file_basename = 'loglikelihood', comparison_dir = comparison_dir, start_iter = start_iter, latex_report = latex_report)

    logger.info("Generating non-linearity stats plots")
    GenerateNonlinStatsPlots(exp_dir, output_dir, plot, comparison_dir = comparison_dir, start_iter = start_iter, latex_report = latex_report)

    logger.info("Generating clipped-proportion plots")
    GenerateClippedProportionPlots(exp_dir, output_dir, plot, comparison_dir = comparison_dir, start_iter = start_iter, latex_report = latex_report)

    logger.info("Generating parameter difference plots")
    GenerateParameterDiffPlots(exp_dir, output_dir, plot, comparison_dir = comparison_dir, start_iter = start_iter, latex_report = latex_report)


    if plot and latex_report is not None:
        has_compiled = latex_report.Close()
        if has_compiled:
            logger.info("Report has been generated. You can find it at the location {0}".format("{0}/report.pdf".format(output_dir)))

def Main():
    args = GetArgs()
    GeneratePlots(args.exp_dir, args.output_dir,
                  comparison_dir = args.comparison_dir,
                  start_iter = args.start_iter,
                  is_chain = args.is_chain)

if __name__ == "__main__":
    Main()
