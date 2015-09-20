// forward slashes don't work well in URI components even when encoded as %2F. Many server side implementations
// still stumble on them. We can encode/decode the string with a simple scheme like:
// 'hi / there / \\ dude / \\f\\b\\\\'.replace(/\\/g, '\\b').replace(/\//g, '\\f').replace(/\\f/g, '/').replace(/\\b/g, '\\');
function encURIComp(str) {
    return encodeURIComponent(str.replace(/\\/g, '\\b').replace(/\//g, '\\f'));
}

function decURIComp(str) {
    return decodeURIComponent(str).replace(/\\f/g, '/').replace(/\\b/g, '\\');
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
        .range([yAxisSize, width]);
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

    this.updateHaplotypes = function(haploData) {
        console.log(haploData);
        plotContentsGroup.selectAll("*").remove();
        plotContentsGroup.selectAll(".bar")
                .data(chrSizes)
            .enter().append("rect")
                .attr("class", "bar")
                .attr("x", function(d) { return genomeScale(d.startPos); })
                .attr("y", function(d) { return chrOrdinalScale(d.chr); })
                .attr("height", chrOrdinalScale.rangeBand()) //function(d) { return height - y(d.value); })
                .attr("width", function(d) {return genomeScale(d.size)}); //x.rangeBand());
        $.each(haploData.viterbi_haplotypes, function(chr, haplos) {
            haplos.forEach(function(currHaplo) {
                if(currHaplo.haplotype_index_1 === currHaplo.haplotype_index_2) {
                    plotContentsGroup.append("rect")
                        .attr("class", "bar")
                        .attr("x", genomeScale(currHaplo.start_position_bp))
                        .attr("y", chrOrdinalScale(chr))
                        .attr("height", chrOrdinalScale.rangeBand())
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
                } else {
                    plotContentsGroup.append("rect")
                        .attr("class", "bar")
                        .attr("x", genomeScale(currHaplo.start_position_bp))
                        .attr("y", chrOrdinalScale(chr))
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
                    plotContentsGroup.append("rect")
                        .attr("class", "bar")
                        .attr("x", genomeScale(currHaplo.start_position_bp))
                        .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                        .attr("height", chrOrdinalScale.rangeBand() / 2.0)
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
                }
            });
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
