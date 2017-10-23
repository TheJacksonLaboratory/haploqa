// forward slashes don't work well in URI components even when encoded as %2F. Many server side implementations
// still stumble on them. We can encode/decode the string with a simple scheme like:
// 'hi / there / \\ dude / \\f\\b\\\\'.replace(/\\/g, '\\b').replace(/\//g, '\\f').replace(/\\f/g, '/').replace(/\\b/g, '\\');
function encURIComp(str) {
    return encodeURIComponent(str.replace(/\\/g, '\\b').replace(/\//g, '\\f'));
}

function decURIComp(str) {
    return decodeURIComponent(str).replace(/\\f/g, '/').replace(/\\b/g, '\\');
}

var entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
};

/**
 * escapeHtml copied from mustache.js which uses the MIT License
 */
function escapeHtml(string) {
    return String(string).replace(/[&<>"'`=\/]/g, function fromEntityMap(s) {
        return entityMap[s];
    });
}

function deepCopyObj(obj) {
    return $.extend(true, {}, obj);
}

function showConfirmMessage(msg) {
    var modalDialog = $('#confirm-modal');
    modalDialog.modal();
    $('#confirm-modal-message').text(msg);
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

function discardDupElems(arr, elemToIdStr) {
    var seenIdStrs = {};
    return arr.filter(function(elem) {
        var str = elem;
        if(elemToIdStr) {
            str = elemToIdStr(elem);
        }

        if(seenIdStrs.hasOwnProperty(str)) {
            return false;
        } else {
            seenIdStrs[str] = null;
            return true;
        }
    });
}

/**
 * A little "class" to help out with tri state checkboxes.
 */
function TriStateCheckbox(checkbox) {
    var self = this;

    var checkedVal = checkbox.prop("checked");
    var indeterminatePropName = "indeterminate";

    /**
     * Set this to a function value that should be called when the state changes. This event
     * will not be fired in response to programatic state changes (via the checked function)
     */
    this.onTriStateChanged = null;

    /**
     * Get or set the checked state of this checkbox. The checked val can be true, false or
     * null (which represents the indeterminate state)
     * @param {boolean} [val]
     * @return {boolean} iff this function is called with no val argument the current state is returned
     */
    this.checked = function(val) {
        if(typeof val === 'undefined') {
            return checkedVal;
        } else {
            checkedVal = val;
            oldCheckedVal = checkedVal;
            if(val === null) {
                checkbox.prop(indeterminatePropName, true);
                checkbox.prop("checked", false);
            } else {
                checkbox.prop(indeterminatePropName, false);
                checkbox.prop("checked", val);
            }
        }
    };

    var oldCheckedVal = checkedVal;
    var changeFunc = function() {
        checkbox.prop(indeterminatePropName, false);
        checkedVal = checkbox.prop("checked");

        // don't do anything if the value hasn't changed
        if(checkedVal !== oldCheckedVal) {
            oldCheckedVal = checkedVal;

            // notify the listener
            if(self.onTriStateChanged) {
                self.onTriStateChanged();
            }
        }
    };

    checkbox.on("change", changeFunc);
}

/**
 * a class to simplify working with bootstrap dropdowns. For this to work all of the clickable
 * 'a' element must have a 'data-value' attribute. These values must correspond to the string
 * values used in the value getter/setter function. Any item under dropdownDiv with an
 * data-dropdown-label will have its text set to match the text of the selected 'a'
 * @param dropdownDiv
 *      the 'div' containing the 'button' and 'ul' elements for the dropdown.
 * @constructor
 */
function BootstrapDropdown(dropdownDiv) {
    var self = this;
    var value = null;
    var opts = dropdownDiv.find('a[data-value]');
    var ddLbls = dropdownDiv.find('[data-dropdown-label]')

    this.getValue = function() {
        return value;
    };

    this.setValue = function(val) {
        value = val;
        if(val !== null) {
            ddLbls.text(dropdownDiv.find('a[data-value="' + val + '"]').text());
        }
    };

    this.onChange = null;

    opts.click(function(e) {
        e.preventDefault();

        var newVal = $(this).attr('data-value');
        self.setValue(newVal);
        if(self.onChange) {
            self.onChange();
        }
    });

    self.setValue(opts.first().attr('data-value'));
}

/**
 * A small wrapper around setTimeout that allows for preemption.
 * @constructor
 */
function DelayedPreemptable() {
    var timeoutID = null;
    this.delay = function(func, delayMillisecs) {
        if(timeoutID !== null) {
            window.clearTimeout(timeoutID);
            timeoutID = null;
        }

        if(typeof delayMillisecs === 'undefined' || delayMillisecs === 0) {
            func();
        } else {
            timeoutID = window.setTimeout(func, delayMillisecs);
        }
    };
}

function ElemOverlay(targetElement, centerSpan) {
    var overlay = null;
    this.overlayActive = function(setActive) {
        if(typeof setActive === 'undefined') {
            return overlay !== null;
        } else if(setActive) {
            if(overlay == null) {
                var offset = targetElement.offset();
                overlay = $(document.createElement('div'));

                overlay.css(offset);
                overlay.width(targetElement.outerWidth());
                overlay.height(targetElement.outerHeight());
                overlay.addClass('elem-overlay');

                //var textSpan = $(document.createElement('span'));
                //textSpan.text(centerSpan);
                //waitOverlay.append(textSpan);
                overlay.append(centerSpan);

                $('body').append(overlay);
            }
        } else {
            if(overlay !== null) {
                overlay.remove();
                overlay = null;
            }
        }
    };
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
            var mouseXY = d3.mouse(svg.node());
            var x = mouseXY[0];
            var y = mouseXY[1];
            var bpPos = null;
            var chr = null;

            if(genomeScale !== null && chrOrdinalScale !== null) {
                bpPos = genomeScale.invert(x);

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
    var cachedHaplotypeMap = {};
    var cachedStrainNames = null;
    var plotContentsGroup = svg.append("g").attr("class", "plot-contents");
    this.updateHaplotypes = function(haploData, haplotypeMap, strainNames) {
        if(typeof haploData === 'undefined') {
            haploData = cachedHaplotypeData;
        } else {
            cachedHaplotypeData = haploData;
        }

        if(typeof haplotypeMap === 'undefined') {
            haplotypeMap = cachedHaplotypeMap;
        } else {
            cachedHaplotypeMap = haplotypeMap;
        }

        if(typeof strainNames == 'undefined') {
            strainNames = cachedStrainNames;
        } else {
            cachedStrainNames = strainNames;
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
                    var currStrain1 = haploData.contributing_strains[currHaplo.haplotype_index_1];
                    var currStrainIdx1 = strainNames.indexOf(currStrain1);
                    var currStrain2 = haploData.contributing_strains[currHaplo.haplotype_index_2];
                    var currStrainIdx2 = strainNames.indexOf(currStrain2);

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
                    if(currHaplo.haplotype_index_1 === currHaplo.haplotype_index_2) {
                        currRect = plotContentsGroup.append("rect")
                            .attr("class", "bar")
                            .attr("x", genomeScale(currHaploStart))
                            //.attr("y", chrOrdinalScale(chr))
                            //.attr("height", chrOrdinalScale.rangeBand())
                            .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                            .attr("height", chrOrdinalScale.rangeBand() / 2.0)
                            .attr("width", genomeScale(currHaploEnd) - genomeScale(currHaploStart))
                            .attr("class", "hap hap" + currStrainIdx1)
                            .on("mouseover", function() {
                                if(self.mouseOverHaplotype !== null) {
                                    self.mouseOverHaplotype(currStrain1);
                                }
                            }).on("mouseout", function() {
                                if(self.mouseOutHaplotype !== null) {
                                    self.mouseOutHaplotype(currStrain1);
                                }
                            });
                        if(haplotypeMap.hasOwnProperty(currStrain1)) {
                            currRect.style('fill', haplotypeMap[currStrain1].color);
                        }
                    } else {
                        // TODO these bars may be flipped!
                        currRect = plotContentsGroup.append("rect")
                            .attr("class", "bar")
                            .attr("x", genomeScale(currHaploStart))
                            //.attr("y", chrOrdinalScale(chr))
                            //.attr("height", chrOrdinalScale.rangeBand() / 2.0)
                            .attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                            .attr("height", chrOrdinalScale.rangeBand() / 4.0)
                            .attr("width", genomeScale(currHaploEnd) - genomeScale(currHaploStart))
                            .attr("class", "hap hap" + currStrainIdx1)
                            .on("mouseover", function() {
                                if(self.mouseOverHaplotype !== null) {
                                    self.mouseOverHaplotype(currStrain1);
                                }
                            }).on("mouseout", function() {
                                if(self.mouseOutHaplotype !== null) {
                                    self.mouseOutHaplotype(currStrain1);
                                }
                            });
                        if(haplotypeMap.hasOwnProperty(currStrain1)) {
                            currRect.style('fill', haplotypeMap[currStrain1].color);
                        }

                        currRect = plotContentsGroup.append("rect")
                            .attr("class", "bar")
                            .attr("x", genomeScale(currHaploStart))
                            //.attr("y", chrOrdinalScale(chr) + (chrOrdinalScale.rangeBand() / 2.0))
                            //.attr("height", chrOrdinalScale.rangeBand() / 2.0)
                            .attr("y", chrOrdinalScale(chr) + (3.0 * chrOrdinalScale.rangeBand() / 4.0))
                            .attr("height", chrOrdinalScale.rangeBand() / 4.0)
                            .attr("width", genomeScale(currHaploEnd) - genomeScale(currHaploStart))
                            .attr("class", "hap hap" + currStrainIdx2)
                            .on("mouseover", function() {
                                if(self.mouseOverHaplotype !== null) {
                                    self.mouseOverHaplotype(currStrain2);
                                }
                            }).on("mouseout", function() {
                                if(self.mouseOutHaplotype !== null) {
                                    self.mouseOutHaplotype(currStrain2);
                                }
                            });
                        if(haplotypeMap.hasOwnProperty(currStrain2)) {
                            currRect.style('fill', haplotypeMap[currStrain2].color);
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

    this.drawLegend = function(strainMap, contributingStrains) {
        var legend = svg.append("g")
            .attr("class", "plot-legend")
            .attr("transform", "translate(30, 900)");

        var translateX = 0;
        contributingStrains.forEach(function(e) {
            var name = e;
            var color = strainMap[e].color;

            var width = 13 + (name.length * 7) + 10;

            var keyElement = legend.append("g")
                .attr("id", "svg-" + name)
                .attr("transform", "translate(" + translateX + ", 10)");

            keyElement.append("rect")
                .attr("width", 10)
                .attr("height", 10)
                .style("fill", color);

            keyElement.append("text")
                .attr("transform", "translate(13, 10)")
                .style("font-size", 12)
                .html(name);

            translateX += width;

        })
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


function StripPlot(svgNode) {
    // we define "self" here because the meaning of "this" can easily change with context
    var self = this;

    var svg = d3.select(svgNode);

    // We create this root so that we can safely do a plot
    var plotRoot = svg.append('g').classed('plot-content', true);

    // this ratio determines how much white space we leave between min/max values and the end of the axis
    var dataAxisMarginRatio = 0.05;

    /**
     * Render the plot
     * @param {number} [params.paddingPx=10] the amount of padding to leave around the plot in pixels
     * @param {string} [params.title] the plot label (appears over the plot)
     * @param params.widthPx the width of the SVG canvas
     * @param params.heightPx the width of the SVG canvas
     * @param {number} [params.pointSizePx=5] the default size used for point shapes
     */
    this.render = function(params) {
        plotRoot.selectAll('*').remove();

        var gemmIntens = params.gemmIntens;

        var title = params.title;
        if(typeof title === 'undefined') {
            title = null;
        }

        var widthPx = params.widthPx;
        var heightPx = params.heightPx;

        var paddingPx = params.paddingPx;
        if(typeof paddingPx === 'undefined') {
            paddingPx = 10;
        }

        var pointSizePx = params.pointSizePx;
        if(typeof pointSizePx === 'undefined') {
            pointSizePx = 5;
        }

        var yAxisLabel = params.yAxisLabel;
        if(typeof yAxisLabel === 'undefined') {
            yAxisLabel = 'Value';
        }

        var leftAxisPadding = paddingPx + 50;
        var rightAxisPadding = paddingPx;
        var topAxisPadding = paddingPx;
        var bottomAxisPadding = paddingPx + 100;

        var maxVal = null;
        var minVal = null;
        var gemmProbeIntens = [];
        $.each(gemmIntens, function(gemmTgt, gemmTgtProbes) {
            gemmTgtProbes.forEach(function(gemmTgtProbe) {
                var currProbe = {
                    gemmTarget: gemmTgt,
                    gemmProbeId: gemmTgtProbe['snp_id'],
                    nonCtrlIntens: gemmTgtProbe['non_ctrls'],
                    posCtrlIntens: gemmTgtProbe['pos_ctrls'],
                    negCtrlIntens: gemmTgtProbe['neg_ctrls']
                };
                gemmProbeIntens.push(currProbe);
                var allProbeIntens = currProbe.nonCtrlIntens.concat(currProbe.posCtrlIntens);
                allProbeIntens = allProbeIntens.concat(currProbe.negCtrlIntens);
                allProbeIntens.forEach(function(intens) {
                    if(maxVal === null || intens.probe_intensity > maxVal) {
                        maxVal = intens.probe_intensity;
                    }

                    if(minVal === null || intens.probe_intensity < minVal) {
                        minVal = intens.probe_intensity;
                    }
                });
            });
        });

        // Create the X scale and axis objects
        var leftmostXAxisPixel = leftAxisPadding;
        var rightmostXAxisPixel = widthPx - (leftAxisPadding + rightAxisPadding);
        var spacingPerProbe = (rightmostXAxisPixel - leftmostXAxisPixel) / gemmProbeIntens.length;
        var xScale = d3.scale.ordinal()
            .domain(gemmProbeIntens.map(function(probe) {return probe.gemmProbeId;}))
            .rangePoints([leftmostXAxisPixel + spacingPerProbe / 2.0, rightmostXAxisPixel - spacingPerProbe / 2.0]);
        var xAxis = d3.svg.axis()
            .scale(xScale)
            .orient('bottom');
        var xAxisGrp = plotRoot.append('g').classed('axis x-axis', true).call(xAxis);
        xAxisGrp.attr('transform', 'translate(0, ' + (heightPx - bottomAxisPadding) + ')');
        xAxisGrp.selectAll('text')
            .attr("y", 0)
            .attr("x", -9)
            .attr("transform", function() {
                return "translate(" + (-this.getBBox().height / 2.0) + ")rotate(-90)";
            })
            .style("text-anchor", "end")
            .style("dominant-baseline", "middle");
        xAxisGrp.selectAll('.domain').remove();
        var bottomPixel = heightPx - bottomAxisPadding;
        xAxisGrp.append('line')
            .attr('x1', leftmostXAxisPixel)
            .attr('x2', rightmostXAxisPixel)
            .classed('domain', true);

        // Create the Y scale and axis objects
        var topPixel = topAxisPadding;
        var dataMargin = 0;
        if(dataAxisMarginRatio > 0) {
            dataMargin = (maxVal - minVal) * dataAxisMarginRatio;
        }

        var yAxisLabelGrp = plotRoot.append('g');
        yAxisLabelGrp.append('text')
            .classed('axis-label y-axis-label', true)
            .html(yAxisLabel)
            .style('text-anchor', 'middle')
            .attr('transform', function() {
                return 'translate(' + this.getBBox().height + ', ' + ((topPixel + bottomPixel) / 2.0) + ')rotate(-90)';
            });

        var yScale = d3.scale.linear()
            .domain([minVal - dataMargin, maxVal + dataMargin])
            .range([bottomPixel, topPixel]);
        var yAxis = d3.svg.axis()
            .scale(yScale)
            .orient('left');
        var yAxisGrp = plotRoot.append('g').classed('axis y-axis', true).call(yAxis);
        yAxisGrp.attr('transform', 'translate(' + leftAxisPadding + ')');


        var pointsGrp = plotRoot.append('g').classed('points', true);

        var probeKindStyle = {
            nonCtrlIntens: {
                className: 'sample-point',
                offset: 0
            },
            posCtrlIntens: {
                className: 'pos-ctrl-point',
                offset: pointSizePx * 4
            },
            negCtrlIntens: {
                className: 'neg-ctrl-point',
                offset: -pointSizePx * 4
            }
        };
        gemmProbeIntens.forEach(function(currProbe) {
            $.each(probeKindStyle, function(probeKind, probeStyle) {
                currProbe[probeKind].forEach(function(currDataPoint) {
                    var pointLink = pointsGrp.append('a')
                        .attr('xlink:href', '/sample/' + currDataPoint.sample_obj_id + '.html');
                    pointLink.append('circle')
                        .attr('r', pointSizePx)
                        .attr('cx', function() {
                            return xScale(currProbe.gemmProbeId) + probeStyle.offset;
                        })
                        .attr('cy', yScale(currDataPoint.probe_intensity))
                        .classed('data-point', true)
                        .classed(probeStyle.className, true)
                        .on('mouseover', function() {
                            if(self.mouseOverPoint) {
                                self.mouseOverPoint(currProbe, currDataPoint);
                            }
                        })
                        .on('mouseout', function() {
                            if(self.mouseOutPoint) {
                                self.mouseOutPoint(currProbe, currDataPoint);
                            }
                        })
                        .on('mousemove', function() {
                            if(self.mouseMovePoint) {
                                self.mouseMovePoint(currProbe, currDataPoint);
                            }
                        });
                });
            });
        });

        this.mouseOverPoint = null;
        this.mouseOutPoint = null;
        this.mouseMovePoint = null;
    };
}
