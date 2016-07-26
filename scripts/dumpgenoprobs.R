#!/usr/bin/Rscript
library(methods)
library(h5)

sampleFilePattern <- "^(.+)\\.genotype\\.probs\\.Rdata$"
codeStrainList <- list(
    A='A/J',
    B='C57BL/6J',
    C='129S1/SvImJ',
    D='NOD/ShiLtJ',
    E='NZO/HlLtJ',
    F='CAST/EiJ',
    G='PWK/PhJ',
    H='WSB/EiJ'
)
ccDiploCodeToStrains <- function(ccDiploCode) {
    code1 <- substr(ccDiploCode, 1, 1)
    code2 <- substr(ccDiploCode, 2, 2)

    c(codeStrainList[[code1]], codeStrainList[[code2]])
}

dump.all <- function(platform, inDir, outFile) {
    if (is.null(inDir) || is.na(outFile))
        stop("inDir can't be null or NA")
    if (!file.info(inDir)$isdir)
        stop("inDir must be a directory")

    dir.create(dirname(outFile), recursive=T, showWarnings=F)
    genoProbH5 <- h5file(outFile, 'a')
    currSampleIndex <- length(list.groups(genoProbH5['samples']))
    currFileIndex <- 1
    allFiles <- list.files(inDir, pattern=sampleFilePattern, recursive=T, ignore.case=T)
    for (f in allFiles) {
        sampleName <- gsub(sampleFilePattern, "\\1", f)
        sampleName <- gsub('.', '-', sampleName, fixed=T)
        sampleName <- gsub('^JAC', '', sampleName)

        currFile <- file.path(inDir, f)
        cat(paste('processing file', currFileIndex, 'of', length(allFiles), currFile), sep='\n')

        load(currFile)

        diplotypeCodes <- colnames(prsmth)
        diplotypeStrains <- matrix("", nrow=length(diplotypeCodes), ncol=2)
        for(i in seq_along(diplotypeCodes)) {
            diplotypeStrains[i, ] <- ccDiploCodeToStrains(diplotypeCodes[i])
        }

        genoProbH5[paste("samples", currSampleIndex, "sample_id", sep="/")] <- sampleName
        genoProbH5[paste("samples", currSampleIndex, "platform", sep="/")] <- platform
        genoProbH5[paste("samples", currSampleIndex, "probeset_ids", sep="/")] <- rownames(prsmth)
        genoProbH5[paste("samples", currSampleIndex, "diplotype_strains", sep="/")] <- diplotypeStrains
        genoProbH5[paste("samples", currSampleIndex, "diplotype_probabilities", sep="/")] <- t(prsmth)

        rm("prsmth")
        currSampleIndex <- currSampleIndex + 1
        currFileIndex <- currFileIndex + 1
    }

    h5close(genoProbH5)
}

cmdArgs <- commandArgs(trailingOnly=T)
if(length(cmdArgs) != 3)
    stop("Usage: dumpgenoprobs.R PLATFORM IN_DIR OUT_FILE")

dump.all(cmdArgs[1], cmdArgs[2], cmdArgs[3])
