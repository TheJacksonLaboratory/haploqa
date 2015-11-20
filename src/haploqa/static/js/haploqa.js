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

function anyResultsPending(haploData) {
    var anyPending = false;
    $.each(haploData.viterbi_haplotypes.chromosome_data, function(chr, haplos) {
        if(haplos.results_pending) {
            anyPending = true;

            // break loop
            return false;
        }
    });

    return anyPending;
}

function parseInterval(intervalStr) {
    var match = intervalStr.match(/^\s*(Chr)?([a-z0-9]+)\s*[:\s]\s*([0-9]+)(Mb)?\s*[-\s]\s*([0-9]+)(Mb)?\s*$/i);
    if(match === null) {
        return null;
    } else {
        var startNum = parseInt(match[3]);
        var startMb = typeof match[4] !== 'undefined';

        var endNum = parseInt(match[5]);
        var endMb = typeof match[6] !== 'undefined';

        var interval = {
            chr: match[2],
            startPos: startMb ? startNum * 1000000 : startNum,
            endPos: endMb ? endNum * 1000000 : endNum
        };

        interval.size = interval.endPos - interval.startPos + 1;

        return interval;
    }
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
 * @param {number} [params.initZoomWidthBp=10000000]
 *          the width in basepairs that we zoom into when a user clicks on the karyotype
 * @param {boolean} [params.intervalMode=false]
 *          in interval mode this plot just shows a single interval and allows zooming/panning within the plot.
 *          Otherwise we render the entire genome karyotype.
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
    var chrSizesHash = {};
    chrSizes.forEach(function(currChr) {
        if(minStartBp === null || currChr.startPos < minStartBp) {
            minStartBp = currChr.startPos;
        }

        var currEnd = currChr.startPos + currChr.size;
        if(maxEndBp === null || currEnd > maxEndBp) {
            maxEndBp = currEnd;
        }

        chrIDs.push(currChr.chr);
        chrSizesHash[currChr.chr] = currChr;
    });

    var xAxisSize = 50;
    var yAxisSize = 50;

    var intervalMode = false;
    if(typeof params.intervalMode !== 'undefined') {
        intervalMode = params.intervalMode;
    }

    var initZoomWidthBp = 10000000 - 1;
    if(typeof params.initZoomWidthBp !== 'undefined') {
        initZoomWidthBp = params.initZoomWidthBp;
    }

    var _zoomInterval = null;
    this.zoomInterval = function(newZoomInterval) {
        if(typeof newZoomInterval === 'undefined') {
            return _zoomInterval;
        } else {
            _zoomInterval = newZoomInterval;
        }

        // if we're in "intervalMode" a change in interval forces us to re-render
        // all of the haplotype data. Otherwise we just need to re-render the
        // interval overlay used on the global karyotype view.
        if(intervalMode) {
            self.updateHaplotypes();
        } else {
            zoomOverlayGroup.selectAll("*").remove();
        }
    };

    if(intervalMode) {
        var refIntervalMovingX = null;
        var zoomInitStartBp = null;
        var zoomInitWidthBp = null;
        var zoom = d3.behavior.zoom();
        svg.call(zoom);
        zoom.on('zoomstart', function() {
            if(_zoomInterval !== null) {
                zoomInitStartBp = _zoomInterval.startPos;
                zoomInitWidthBp = _zoomInterval.size;
            }
        });
        zoom.on('zoom', function() {
            if(_zoomInterval !== null) {
                var newIntervalSize = Math.round(zoomInitWidthBp / d3.event.scale);
                if(newIntervalSize !== _zoomInterval.size) {
                    _zoomInterval.size = newIntervalSize;
                    var growthBp = newIntervalSize - zoomInitWidthBp;
                    _zoomInterval.startPos = zoomInitStartBp - Math.round(growthBp / 2);
                    // TODO what about this - 1. Do we need it?
                    _zoomInterval.endPos = _zoomInterval.startPos + _zoomInterval.size - 1;
                    self.zoomIntervalChange(_zoomInterval);
                }
            }
        });
        zoom.on('zoomend', function() {
            zoom.scale(1);
        });
        svg.on('mousedown', function() {
            var mouseXY = d3.mouse(svg.node());
            var x = mouseXY[0];

            // user is clicking on the reference chromosome
            if(_zoomInterval !== null) {
                refIntervalMovingX = x;
            }
            d3.event.preventDefault();
        });

        svg.on('mousemove', function() {
            var mouseXY = d3.mouse(svg.node());
            var x = mouseXY[0];
            if(refIntervalMovingX !== null) {
                var prevRefMousePosBp = genomeScale.invert(refIntervalMovingX);
                var newRefMousePosBp = genomeScale.invert(x);
                _zoomInterval.startPos += Math.round(prevRefMousePosBp - newRefMousePosBp);
                // TODO what about this - 1. Do we need it?
                _zoomInterval.endPos = _zoomInterval.startPos + _zoomInterval.size - 1;
                self.zoomIntervalChange(_zoomInterval);

                refIntervalMovingX = x;
            }
        });

        svg.on('mouseup', function() {
            refIntervalMovingX = null;
        });
    } else {
        svg.on('click', function() {
            console.log('svg clicked');
            var mouseXY = d3.mouse(svg.node());
            var x = mouseXY[0];
            var y = mouseXY[1];
            var bpPos = null;
            var chr = null;

            if(genomeScale !== null && chrOrdinalScale !== null) {
                bpPos = genomeScale.invert(x);
                console.log(bpPos);

                // we have no built in revert for ordinal scale so we'll do that ourselves
                var ordinalHeight = chrOrdinalScale.rangeBand();
                yAxisIDs.some(function(currChr) {
                    var currY = chrOrdinalScale(currChr);
                    if(y >= currY && y <= currY + ordinalHeight) {
                        chr = currChr;

                        // break
                        return true;
                    }
                });
                console.log(chr);
            }

            if(bpPos !== null && chr !== null) {
                if(_zoomInterval === null) {
                    _zoomInterval = {size: initZoomWidthBp};
                }

                _zoomInterval.chr = chr;
                _zoomInterval.startPos = Math.round(bpPos - _zoomInterval.size / 2.0);
                _zoomInterval.endPos = _zoomInterval.startPos + _zoomInterval.size - 1;

                if(self.zoomIntervalChange !== null) {
                    self.zoomIntervalChange(_zoomInterval);
                }
            }
        });
    }

    this.zoomIntervalChange = null;

    var cachedHaplotypeData = null;
    var cachedHaplotypeColors = {};
    var plotContentsGroup = svg.append("g").attr("class", "plot-contents");
    this.updateHaplotypes = function(haploData, haplotypeColors) {
        if(typeof haploData === 'undefined') {
            haploData = cachedHaplotypeData;
        } else {
            cachedHaplotypeData = haploData;
        }

        if(typeof haplotypeColors === 'undefined') {
            haplotypeColors = cachedHaplotypeColors;
        } else {
            cachedHaplotypeColors = haplotypeColors;
        }

        plotContentsGroup.selectAll("*").remove();

        if(intervalMode) {
            updateAxes();
            if(_zoomInterval === null) {
                return;
            }
        }

        if(haploData === null) {
            return;
        }

        if(!intervalMode) {
            plotContentsGroup.selectAll(".bar")
                .data(chrSizes)
                .enter().append("rect")
                .attr("class", "bar")
                .attr("x", function(d) {
                    return genomeScale(d.startPos);
                })
                .attr("y", function(d) {
                    return chrOrdinalScale(d.chr);
                })
                .attr("height", chrOrdinalScale.rangeBand()) //function(d) { return height - y(d.value); })
                .attr("width", function(d) {
                    return genomeScale(d.size)
                }); //x.rangeBand());
        }

        yAxisIDs.forEach(function(chr) {
            if(!(chr in haploData.viterbi_haplotypes.chromosome_data)) {
                return;
            }
            var haplos = haploData.viterbi_haplotypes.chromosome_data[chr];
            var currChrSize = chrSizesHash[chr];

            if(haplos.haplotype_blocks) {
                haplos.haplotype_blocks.forEach(function(currHaplo) {
                    var currHaploStart;
                    var currHaploEnd;
                    if(intervalMode) {
                        currHaploStart = Math.max(currHaplo.start_position_bp, _zoomInterval.startPos);
                        currHaploEnd = Math.min(currHaplo.end_position_bp, _zoomInterval.startPos + _zoomInterval.size);
                    } else {
                        currHaploStart = Math.max(currHaplo.start_position_bp, currChrSize.startPos);
                        currHaploEnd = Math.min(currHaplo.end_position_bp, currChrSize.startPos + currChrSize.size);
                    }

                    if(currHaploStart >= currHaploEnd) {
                        return;
                    }

                    var currRect;
                    var currHapID;
                    if(currHaplo.haplotype_index_1 === currHaplo.haplotype_index_2) {
                        currHapID = haploData.haplotype_samples[currHaplo.haplotype_index_1].obj_id;
                        currRect = plotContentsGroup.append("rect")
                            .attr("class", "bar")
                            .attr("x", genomeScale(currHaploStart))
                            //.attr("y", chrOrdinalScale(chr))
                            //.attr("height", chrOrdinalScale.rangeBand())
                            .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                            .attr("height", chrOrdinalScale.rangeBand() / 2.0)
                            .attr("width", genomeScale(currHaploEnd) - genomeScale(currHaploStart))
                            .attr("class", "hap hap" + currHapID)
                            .on("mouseover", function() {
                                if(self.mouseOverHaplotype !== null) {
                                    self.mouseOverHaplotype(currHaplo.haplotype_index_1, haploData);
                                }
                            }).on("mouseout", function() {
                                if(self.mouseOutHaplotype !== null) {
                                    self.mouseOutHaplotype(currHaplo.haplotype_index_1, haploData);
                                }
                            });
                        if(haplotypeColors.hasOwnProperty(currHapID)) {
                            currRect.style('fill', haplotypeColors[currHapID]);
                        }
                    } else {
                        // TODO these bars may be flipped!
                        currHapID = haploData.haplotype_samples[currHaplo.haplotype_index_1].obj_id;
                        currRect = plotContentsGroup.append("rect")
                            .attr("class", "bar")
                            .attr("x", genomeScale(currHaploStart))
                            //.attr("y", chrOrdinalScale(chr))
                            //.attr("height", chrOrdinalScale.rangeBand() / 2.0)
                            .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                            .attr("height", chrOrdinalScale.rangeBand() / 4.0)
                            .attr("width", genomeScale(currHaploEnd) - genomeScale(currHaploStart))
                            .attr("class", "hap hap" + currHapID)
                            .on("mouseover", function() {
                                if(self.mouseOverHaplotype !== null) {
                                    self.mouseOverHaplotype(currHaplo.haplotype_index_1, haploData);
                                }
                            }).on("mouseout", function() {
                                if(self.mouseOutHaplotype !== null) {
                                    self.mouseOutHaplotype(currHaplo.haplotype_index_1, haploData);
                                }
                            });
                        if(haplotypeColors.hasOwnProperty(currHapID)) {
                            currRect.style('fill', haplotypeColors[currHapID]);
                        }

                        currHapID = haploData.haplotype_samples[currHaplo.haplotype_index_2].obj_id;
                        currRect = plotContentsGroup.append("rect")
                            .attr("class", "bar")
                            .attr("x", genomeScale(currHaploStart))
                            //.attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                            //.attr("height", chrOrdinalScale.rangeBand() / 2.0)
                            .attr("y", chrOrdinalScale(chr) + (3.0 * chrOrdinalScale.rangeBand() / 4.0))
                            .attr("height", chrOrdinalScale.rangeBand() / 4.0)
                            .attr("width", genomeScale(currHaploEnd) - genomeScale(currHaploStart))
                            .attr("class", "hap hap" + currHapID)
                            .on("mouseover", function() {
                                if(self.mouseOverHaplotype !== null) {
                                    self.mouseOverHaplotype(currHaplo.haplotype_index_2, haploData);
                                }
                            }).on("mouseout", function() {
                                if(self.mouseOutHaplotype !== null) {
                                    self.mouseOutHaplotype(currHaplo.haplotype_index_2, haploData);
                                }
                            });
                        if(haplotypeColors.hasOwnProperty(currHapID)) {
                            currRect.style('fill', haplotypeColors[currHapID]);
                        }
                    }
                });
            }

            if(haplos.concordance_bins) {
                haplos.concordance_bins.forEach(function(currBin) {
                    var currBinStart;
                    var currBinEnd;
                    if(intervalMode) {
                        currBinStart = Math.max(currBin.start_position_bp, _zoomInterval.startPos);
                        currBinEnd = Math.min(currBin.end_position_bp, _zoomInterval.startPos + _zoomInterval.size);
                    } else {
                        currBinStart = Math.max(currBin.start_position_bp, currChrSize.startPos);
                        currBinEnd = Math.min(currBin.end_position_bp, currChrSize.startPos + currChrSize.size);
                    }

                    if(currBinStart >= currBinEnd) {
                        return;
                    }

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
                        .attr("x", genomeScale(currBinStart))
                        .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0) - height)
                        .attr("height", height)
                        .attr("width", genomeScale(currBinEnd) - genomeScale(currBinStart));
                });
            }
        });
    };

    var axesGroup = svg.append("g").attr("class", "axes");
    var genomeScale = null;
    var chrOrdinalScale = null;
    var yAxisIDs;
    function updateAxes() {
        axesGroup.selectAll("*").remove();
        if(intervalMode && _zoomInterval === null) {
            return;
        }

        var startBp;
        var endBp;
        if(intervalMode) {
            startBp = _zoomInterval.startPos;
            endBp = _zoomInterval.startPos + _zoomInterval.size;
            yAxisIDs = [_zoomInterval.chr];
        } else {
            startBp = minStartBp;
            endBp = maxEndBp;
            yAxisIDs = chrIDs;
        }

        genomeScale = d3.scale.linear()
            .domain([startBp, endBp])
            .range([yAxisSize, width - yAxisSize - 2]);
        var genomeAxis = d3.svg.axis()
            .scale(genomeScale)
            .orient("bottom")
            .tickFormat(function(x) {return (x / 1000000) + ' Mb';});
        axesGroup.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + (height - xAxisSize) + ")")
            .call(genomeAxis);

        chrOrdinalScale = d3.scale.ordinal()
            .domain(yAxisIDs)
            .rangeRoundBands([0, height - xAxisSize], intervalMode ? 0.0 : 0.2);
        var yAxis = d3.svg.axis()
            .scale(chrOrdinalScale)
            .orient("left")
            .tickFormat(function(x) {return 'Chr' + x;});
        axesGroup.append("g")
            .attr("class", "y axis")
            .attr("transform", "translate(" + yAxisSize + ",0)")
            .call(yAxis);
    }
    updateAxes();

    var zoomOverlayGroup = svg.append("g").attr("class", "zoom-overlay");

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
