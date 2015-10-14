// forward slashes don't work well in URI components even when encoded as %2F. Many server side implementations
// still stumble on them. We can encode/decode the string with a simple scheme like:
// 'hi / there / \\ dude / \\f\\b\\\\'.replace(/\\/g, '\\b').replace(/\//g, '\\f').replace(/\\f/g, '/').replace(/\\b/g, '\\');
function encURIComp(str) {
    return encodeURIComponent(str.replace(/\\/g, '\\b').replace(/\//g, '\\f'));
}

function decURIComp(str) {
    return decodeURIComponent(str).replace(/\\f/g, '/').replace(/\\b/g, '\\');
}

function showErrorMessage(msg) {
    var modalDialog = $('#error-modal');
    var errorModalMessage = $('#error-modal-message');
    modalDialog.modal();
    errorModalMessage.text(msg);
}

/**
 * @typedef {Object} GenoInterval
 * @property {string} chr
 * @property {number} startPos
 * @property {number} size
 */

/**
 * A karyotype plot for haplotypes
 * @constructor
 * @param {SVGSVGElement} params.svg
 *          the SVG node
 * @param {number} params.width
 *          the width of the svg node
 * @param {number} params.height
 *          the height of the svg node
 * @param {Array.<GenoInterval>} params.chrSizes
 *          gives the sizes of all chromosomes in the genome
 */
function HaploKaryoPlot(params) {
    var self = this;

    var svg = params.svg;
    var width = params.width;
    var height = params.height;
    var chrSizes = params.chrSizes;

    var chrIDs = [];
    var minStartBp = null;
    var maxEndBp = null;
    chrSizes.forEach(function(currChr) {
        if(minStartBp === null || currChr.startPos < minStartBp) {
            minStartBp = currChr.startPos;
        }

        var currEnd = currChr.startPos + currChr.size;
        if(maxEndBp === null || currEnd > maxEndBp) {
            maxEndBp = currEnd;
        }

        chrIDs.push(currChr.chr);
    });

    var xAxisSize = 50;
    var yAxisSize = 50;

    var genomeScale = d3.scale.linear()
        .domain([minStartBp, maxEndBp])
        .range([yAxisSize, width - yAxisSize - 2]);
    var genomeAxis = d3.svg.axis()
        .scale(genomeScale)
        .orient("bottom");
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + (height - xAxisSize) + ")")
        .call(genomeAxis);

    var chrOrdinalScale = d3.scale.ordinal()
        .domain(chrIDs)
        .rangeRoundBands([0, height - xAxisSize], .1);
    var yAxis = d3.svg.axis()
        .scale(chrOrdinalScale)
        .orient("left");
    svg.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(" + yAxisSize + ",0)")
        .call(yAxis);

    var plotContentsGroup = svg.append("g").attr("id", "plot-contents");
    //chrSizes.forEach(function(d) {
    //    plotContentsGroup.append("rect")
    //            .attr("class", "bar")
    //            .attr("x", genomeScale(d.startPos))
    //            .attr("y", chrOrdinalScale(d.chr))
    //            .attr("height", chrOrdinalScale.rangeBand())
    //            .attr("width", genomeScale(d.size));
    //});

    this.updateHaplotypes = function(haploData, haplotypeColors) {
        if(typeof haplotypeColors === 'undefined') {
            haplotypeColors = {};
        }

        plotContentsGroup.selectAll("*").remove();
        plotContentsGroup.selectAll(".bar")
                .data(chrSizes)
            .enter().append("rect")
                .attr("class", "bar")
                .attr("x", function(d) { return genomeScale(d.startPos); })
                .attr("y", function(d) { return chrOrdinalScale(d.chr); })
                .attr("height", chrOrdinalScale.rangeBand()) //function(d) { return height - y(d.value); })
                .attr("width", function(d) {return genomeScale(d.size)}); //x.rangeBand());
        $.each(haploData.viterbi_haplotypes.chromosome_data, function(chr, haplos) {
            haplos.haplotype_blocks.forEach(function(currHaplo) {
                var currRect;
                var currHapID;
                if(currHaplo.haplotype_index_1 === currHaplo.haplotype_index_2) {
                    currRect = plotContentsGroup.append("rect")
                        .attr("class", "bar")
                        .attr("x", genomeScale(currHaplo.start_position_bp))
                        //.attr("y", chrOrdinalScale(chr))
                        //.attr("height", chrOrdinalScale.rangeBand())
                        .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                        .attr("height", chrOrdinalScale.rangeBand() / 2.0)
                        .attr("width", genomeScale(currHaplo.end_position_bp) - genomeScale(currHaplo.start_position_bp))
                        .attr("class", "hap" + (currHaplo.haplotype_index_1 + 1))
                        .on("mousemove", function() {
                            if(self.mouseOverHaplotype !== null) {
                                self.mouseOverHaplotype(currHaplo, haploData);
                            }
                        }).on("mouseout", function() {
                            if(self.mouseOutHaplotype !== null) {
                                self.mouseOutHaplotype(currHaplo, haploData);
                            }
                        });
                    currHapID = haploData.haplotype_samples[currHaplo.haplotype_index_1].obj_id;
                    if(haplotypeColors.hasOwnProperty(currHapID)) {
                        currRect.style('fill', haplotypeColors[currHapID]);
                    }
                } else {
                    // TODO these bars may be flipped!
                    currRect = plotContentsGroup.append("rect")
                        .attr("class", "bar")
                        .attr("x", genomeScale(currHaplo.start_position_bp))
                        //.attr("y", chrOrdinalScale(chr))
                        //.attr("height", chrOrdinalScale.rangeBand() / 2.0)
                        .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                        .attr("height", chrOrdinalScale.rangeBand() / 4.0)
                        .attr("width", genomeScale(currHaplo.end_position_bp) - genomeScale(currHaplo.start_position_bp))
                        .attr("class", "hap" + (currHaplo.haplotype_index_1 + 1))
                        .on("mousemove", function() {
                            if(self.mouseOverHaplotype !== null) {
                                self.mouseOverHaplotype(currHaplo, haploData);
                            }
                        }).on("mouseout", function() {
                            if(self.mouseOutHaplotype !== null) {
                                self.mouseOutHaplotype(currHaplo, haploData);
                            }
                        });
                    currHapID = haploData.haplotype_samples[currHaplo.haplotype_index_1].obj_id;
                    if(haplotypeColors.hasOwnProperty(currHapID)) {
                        currRect.style('fill', haplotypeColors[currHapID]);
                    }

                    currRect = plotContentsGroup.append("rect")
                        .attr("class", "bar")
                        .attr("x", genomeScale(currHaplo.start_position_bp))
                        //.attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                        //.attr("height", chrOrdinalScale.rangeBand() / 2.0)
                        .attr("y", chrOrdinalScale(chr) + (3.0 * chrOrdinalScale.rangeBand() / 4.0))
                        .attr("height", chrOrdinalScale.rangeBand() / 4.0)
                        .attr("width", genomeScale(currHaplo.end_position_bp) - genomeScale(currHaplo.start_position_bp))
                        .attr("class", "hap" + (currHaplo.haplotype_index_2 + 1))
                        .on("mousemove", function() {
                            if(self.mouseOverHaplotype !== null) {
                                self.mouseOverHaplotype(currHaplo, haploData);
                            }
                        }).on("mouseout", function() {
                            if(self.mouseOutHaplotype !== null) {
                                self.mouseOutHaplotype(currHaplo, haploData);
                            }
                        });
                    currHapID = haploData.haplotype_samples[currHaplo.haplotype_index_2].obj_id;
                    if(haplotypeColors.hasOwnProperty(currHapID)) {
                        currRect.style('fill', haplotypeColors[currHapID]);
                    }
                }
            });

            if(haplos.concordance_bins) {
                haplos.concordance_bins.forEach(function(currBin) {
                    var concordanceScore = currBin.concordant_count / currBin.informative_count;
                    concordanceScore -= .5;
                    concordanceScore *= 2;
                    if(concordanceScore < 0) {
                        concordanceScore = 0;
                    }

                    concordanceScore = 1.0 - concordanceScore;
                    var height = concordanceScore * chrOrdinalScale.rangeBand() / 2.0;
                    plotContentsGroup.append("rect")
                        .style('fill', 'red')
                        .attr("x", genomeScale(currBin.start_position_bp))
                        .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0) - height)
                        .attr("height", height)
                        .attr("width", genomeScale(currBin.end_position_bp) - genomeScale(currBin.start_position_bp));
                });
            }
        });
    };

    this.mouseOverHaplotype = null;
    this.mouseOutHaplotype = null;

    /**
     * Uses the d3.mouse function to get the current mouse event and uses the mouse event's xy position
     */
    this.mousePositionInfo = function() {
        var mouseXY = d3.mouse(svg.node());
        var x = mouseXY[0] - self.radius;
        var y = mouseXY[1] - self.radius;

        return {x: x, y: y};
    };
}
