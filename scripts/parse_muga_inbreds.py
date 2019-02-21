#!/usr/bin/env python
"""
Script to take a CSV file containing a list of inbred strain sample for the
MUGA genotyping platform and generate a FinalReport.txt and a Sample_Map.txt
file.  The goal is to put the data into a format that can be uploaded to
HaploQA through the user interface.  The inbred strains are necessary so that
you can set haplotype candidate samples for given strains to be used in
haplotype reconstruction.

The file we are parsing was contributed by Matthew Blanchard at UNC.  UNC
did not have the original sample final report files, but they had loaded
the main data we needed to regenerate.  What we do not have is the sample
detail information that would normally appear in the [Header] section of
a final report file.

This script is really intended to be run once.  It will be committed to
the repository, but the data file is not.  If for some reason you are setting
up a new database and want to regenerate the final report file, contact Dave
Walton or Anna Lamoureux at JAX.

Expected format of the input file is CSV with the following columns:
  sample_id
  group_name
  sample_alias
  sex
  sample_flags
  snp_id
  snp_name
  chromosome
  position
  snp_flags
  call
  x
  y
  gcScore
  theta
  r
  x_raw
  y_raw

Assumption:  The file is ordered by sample_alias and then
by marker.
"""

import argparse
import csv
import logging
import re

logging.basicConfig(filename='parse_muga_inbreds.log', level=logging.INFO)


class FinalReportGenerator(object):
    """
    FinalReportGenerator has a specific purpose for generating MUGA platform
    FinalReport.txt and SampleMap.txt files.
    Usage:
        Instantiate passing name you want to appear in FinalReport.txt filename
            final_report = FinalReportGenerator("MUGA_Inbreds")
        Skip the first line of your input file to drop header
        For each other line call
            final_report.parse_genotype(row)
        REQUIRED - When all rows processed call
            final_report.finalize()
        As this will push the final sample to the report file and close the
        files.
    """

    def __init__(self, report_name):
        """
        FinalReportGenerator constructor
        :param report_name: The name that should appear at the head of the
            final report file e.g. {report_name}_FinalReport.txt
        """
        self.samples_found = []
        # Set up the files we will be generating.
        report_name = "{}_FinalReport.txt".format(report_name)
        sample_map_name = "Sample_Map.txt"
        self.final_report_fd = open(report_name, 'w')
        self.sample_map_fd = open(sample_map_name, 'w')
        logging.debug("Output will be written to {} and {}".
                      format(report_name, sample_map_name))
        self.final_writer = csv.writer(self.final_report_fd, delimiter="\t")
        self.sample_writer = csv.writer(self.sample_map_fd, delimiter="\t")
        # Write header to final report file
        self.final_writer.writerow(["[Data]"])
        self.final_writer.writerow(["SNP Name","Sample ID","Allele1 - Forward",
                                    "Allele2 - Forward","X","Y","GC Score",
                                    "Theta","X Raw","Y Raw","R"])
        # Write header to sample map file
        self.sample_writer.writerow(["Index","Name","ID","Gender","Plate Well",
                                     "Group","Parent1","Parent2","Replicate",
                                     "SentrixPosition"])
        # Init variables for processing one sample at a time
        self.current_sample = None
        # we had to introduce our own sample Id as there were uniqueness
        # problems with sample alias
        self.current_sample_id = None
        self.current_sample_metadata = []
        self.current_sample_data = []

        # Master sample index.  Increment as we process a new sample
        self.sample_index = 0

        self.exp = re.compile('.+?(?=[ ])')

    def parse_genotype(self, entry):
        """
        Core function for processing our samples genotype call by genotype call.
        This method will cause the grouping of entries for one sample, and
        when we've processed all those entries, this will cause the
        sample and it's metadata to be written to the final report and
        sample map files.
        Effects the following attributes of the class:
            current_sample, current_sample_data, and current_sample_metadata
        :param entry: A dictionary containing the following values:
            sample_id, group_name, sample_alias, sex, sample_flags, snp_id,
            snp_name, chromosome, position, snp_flags, call, x, y, gcScore,
            theta, r, x_raw, y_raw
        :return: None
        """
        # clean off white space
        sample_alias = entry['sample_alias'].strip()
        # Remove spaces from sample_alias for id
        sample_id = sample_alias.replace(" ", "")

        # Check to see if the given strain is being processed
        if not self.current_sample:
            # This is the first one, assign and create sample map entry
            self.current_sample = sample_alias
            self.current_sample_id = sample_id
            self.samples_found.append(self.current_sample_id)
            self._create_sample_entry(entry)
        elif self.current_sample != sample_alias:
            # We've changed samples, first write current sample
            self._write_sample()
            # Next reinitialize current sample variables
            self.current_sample = sample_alias
            self.current_sample_id = sample_id
            # there are uniqueness problems, so we append the
            # sample index if it's a dupe
            if self.current_sample_id in self.samples_found:
                logging.debug(self.current_sample_id)
                self.current_sample_id = "{}-{}".\
                    format(self.current_sample_id, self.sample_index)
                logging.debug("now {}".format(self.current_sample_id))
            self.samples_found.append(self.current_sample_id)
            self.current_sample_data = []
            self.current_sample_metadata = []
            # Last add the new sample map entry
            self._create_sample_entry(entry)
        self._add_sample_row(entry)

    def _create_sample_entry(self, entry):
        """
        Private method to put a sample entry into SampleMap.txt
        Effects the "sample_index" and the "current_sample_metadata" attributes
        of the class.
        :param entry: first row of data for a given sample
        :return: None
        """
        sample_meta_data = []
        # We have a new sample, increment index
        self.sample_index += 1
        sample_meta_data.append(self.sample_index)
        sample_meta_data.append(self.current_sample)
        sample_meta_data.append(self.current_sample_id)

        # set sex as a full word: Male, Female or Unknown
        sex = entry['sex']
        if sex == "F":
            sex = "Female"
        elif sex == "M":
            sex = "Male"
        else:
            sex = "Unknown"
        sample_meta_data.append(sex)

        # Next two columns are plate and well, mark them blank
        sample_meta_data.append("")
        sample_meta_data.append("")

        # Set the group to UNC for all samples
        sample_meta_data.append("UNC")

        # Parent1, Parent2, Replicate and SentrixPosition will all be blank
        sample_meta_data.append("")
        sample_meta_data.append("")
        sample_meta_data.append("")
        sample_meta_data.append("")
        self.current_sample_metadata = sample_meta_data

    def _add_sample_row(self, entry):
        """
        Private method to put a samples genotype entry into FinalReport.txt
        Effects the "current_sample_data" attribute of the class.
        :param entry: a row of data for a given sample
        :return: None
        """
        sample_row = []
        # Add sample data in proper forder for final report
        sample_row.append(entry['snp_name'])
        sample_row.append(self.current_sample_id)
        # were not provided with an Allele1 and Allele2, so they'll be the same
        sample_row.append(entry['call'])
        sample_row.append(entry['call'])
        sample_row.append(entry['x'])
        sample_row.append(entry['y'])
        sample_row.append(entry['gcScore'])
        sample_row.append(entry['theta'])
        sample_row.append(entry['x_raw'])
        sample_row.append(entry['y_raw'])
        sample_row.append(entry['r'])

        self.current_sample_data.append(sample_row)

    def _write_sample(self):
        """
        Private method that writes a single sample out to both the
        FinalReport.txt and SampleMap.txt files
        :return: None
        """
        self.sample_writer.writerow(self.current_sample_metadata)
        self.final_writer.writerows(self.current_sample_data)

    def finalize(self):
        """
        REQUIRED in order to get the last sample and close the files.
        :return: None
        """
        # write the final sample
        self._write_sample()
        self.final_report_fd.close()
        self.sample_map_fd.close()


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate 'fake' final report and sample map for inbred"
                    "strains for MUGA platform")
    parser.add_argument('input',
                        help='CSV File with inbred samples')

    args = parser.parse_args()

    # Initialize a final report
    final_report = FinalReportGenerator("MUGA_Inbred")
    line_count = 0
    logging.info("Start processing...")
    with open(args.input) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        next(csv_reader)
        for row in csv_reader:
            # Process each line... This will include writing out to files
            # by sample
            final_report.parse_genotype(row)
            line_count += 1
        logging.info("{} lines processed for {} samples".
                     format(line_count, final_report.sample_index))
    # Writes the final sample and closes files
    final_report.finalize()


if __name__ == '__main__':
    main()