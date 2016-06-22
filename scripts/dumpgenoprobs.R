#!/usr/bin/Rscript

dump.all <- function(inDir = NULL, outDir = NULL) {
    if (is.null(inDir) || is.na(outDir))
        stop("inDir can't be null or NA")
    if (!file.info(inDir)$isdir)
        stop("inDir must be a directory")
    
    if (is.null(outDir) || is.na(outDir))
        stop("outDir can't be null or NA")
    if (!file.exists(outDir))
        dir.create(outDir)
    if (!file.info(outDir)$isdir)
        stop("outDir must be a directory")
    
    for (f in list.files(inDir, pattern="\\.rdata$", recursive=T, ignore.case=T)) {
        currFile <- file.path(inDir, f)
        outFile <- file.path(outDir, f)
		outFile <- paste(substr(outFile, 0, nchar(outFile) - 6), '.txt', sep='')
        if (file.exists(outFile))
            stop(paste("refusing to overwrite", outFile))

		cat(paste('processing:', currFile), sep='\n')
		load(currFile)
		dir.create(dirname(outFile), recursive=T, showWarnings=F)
		mode(prsmth) <- "character"
		prsmth <- cbind(rownames(prsmth), prsmth)
		prsmth <- rbind(colnames(prsmth), prsmth)
		prsmth[1, 1] <- "snp_id"
		write.table(prsmth, file=outFile, sep = "\t", row.names=F, col.names=F)
		rm("prsmth")
    }
}

cmdArgs <- commandArgs(trailingOnly=T)
if(length(cmdArgs) != 2)
    stop("Usage: dumpgenoprobs.R IN_DIR OUT_DIR")

dump.all(cmdArgs[1], cmdArgs[2])
