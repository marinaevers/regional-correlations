<template>
  <div class="card" style="user-select: none;">
    <h5 class="card-header"><a @click="reset">Correlation Heatmap</a>
      <span class="float-right"><small><a @click="show = !show"><span v-if="show">hide</span><span v-else>show</span></a></small></span>
    </h5>
    <div class="card-body" v-show="show">
      <div class="row">
        <div class="col-sm-2">
          <label>Correlation threshold</label>
          <select class="form-control" v-model="selectedThreshold" @change="$emit('change-threshold', selectedThreshold)">
            <option v-for="t in $store.state.vis.thresholds">{{ t }}</option>
          </select>
        </div>
        <div class="col-sm-3">
          <div class="form-group">
            <label>Linkage method</label>
            <select class="form-control" v-model="selectedLinkage" @change="$emit('change-linkage', selectedLinkage)">
              <option>single</option>
              <option>complete</option>
              <option>average</option>
              <option>centroid</option>
              <option>median</option>
              <option>ward</option>
            </select>
          </div>
        </div>

        <div class="col-sm-7">
          <label>Time lags <small>(<a @click="showTimeLags = true" v-if="!showTimeLags">show</a> <a @click="showTimeLags = false" v-else>hide</a>)</small></label>
          <transfer-function @value-selected="setSelectedTimelag" ref="transferFunction" :domain-from="$store.state.vis.timeLagRange[0]" :domain-to="$store.state.vis.timeLagRange[1]" transfer-function="interpolatePiYG"></transfer-function>
        </div>
      </div>
      <div style="display: flex; flex-flow:row wrap;">
        <div :style="`order: 1; height: 1rem; flex: 0 1 100%`">
          <div :style="`padding-left: 50px; display: flex; font-size: ${rectWidth}px;`">
            <div
              :style="`flex-direction:row; width: ${rectWidth}px; line-height:2; font-size: 0.7rem; text-align: center; ${getFontColor(colSegment)};`"
              v-for="colSegment in matrix.col_segments">
              <div style=" transform:rotate(90deg);width:100%;">
              {{ getLabel(colSegment) }}
              </div>
            </div>
          </div>
        </div>
        <div :style="`order: 2; flex: 0 1 50px`">
          <div
            :style="`flex-direction:row; line-height:${rectHeight}px;  height:${rectHeight+0.01}px; font-size: 0.7rem; text-align: center; ${getFontColor(colSegment)}`"
            v-for="colSegment in matrix.col_segments">{{ getLabel(colSegment) }}
          </div>
        </div>
        <div :style="`order: 3; flex: 1; min-height:100px; width: calc(100% - 50px)`">
          <div ref="matrixWrapper" id="matrixWrapper"></div>
          <transfer-function @value-selected="correlationCertaintySelected" ref="transferFunctionCorr" :domain-from="-10" :domain-to="10" transfer-function="interpolateRdBu" :labels="['-1', '0', '1']" :title="'Correlation certainty'"></transfer-function>
<!--          <transfer-function ref="transferFunctionTimeLag" :domain-from="$store.state.vis.timeLagRange[0]" :domain-to="$store.state.vis.timeLagRange[1]" transfer-function="interpolatePiYG" :title="'Time lag'"></transfer-function>-->

        </div>
      </div>

      <segment-label-modal
        @close="resetSegementLabel"
        @okay="assignLabel"
        v-if="selectedSegment !== null"
        :selected-segment="selectedSegment"
        :selected-segment-label="selectedSegmentLabel"
      ></segment-label-modal>
    </div>
    <div class="card-footer" v-show="show">
      <div class="row">
        <div class="col-sm-8">
          {{infoText}}
        </div>
        <div class="col-sm-4">
          <div class="text-right">
            <div class="btn-group">
              <a class="btn btn-sm btn-secondary" @click="onResetSelection" v-if="hasSelection">Reset selection</a>
              <a class="btn btn-sm btn-success" @click="$emit('filter-selection')" v-if="hasSelection">Filter
                selection</a>
              <span v-show="false">{{t}}</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import * as d3 from "d3";
import SegmentFilter from "@/mixins/SegmentFilter";
import SegmentSelection from "@/mixins/SegmentSelection";
import TransferFunction from "./TransferFunction";

export default {
  components: {TransferFunction},
  props: {
    matrix: {type: Object, required: true},
    dimensions: {type: Array, required: true},
    linkage: {type: String, default: 'single'},
    threshold: {type: Number, default: 0.9},
    highlightedSegments: {type: Array, default: () => []},
    labels: {
      type: Object, default: () => {
        return {}
      }
    },
    t: {},
  },
  mixins: [SegmentFilter, SegmentSelection],
  data() {
    return {
      show: true,
      canvas: null,
      width: null,
      height: null,
      rectWidth: null,
      rectHeight: null,
      border: 5,
      selectedSegment: null,
      selectedSegmentLabel: null,
      isBrushing: false,
      brushStart: null,
      brushEnd: null,
      rects: [],
      highlightedSegmentsLocal: [],
      hoverValue: null,
      selectedLinkage: 'single',
      selectedThreshold: 0.9,
      time: 0,
      showTimeLags: false,
      infoText: '',
      selectedTimeLag: null,
      selectedCorrelationCertainty: null
    }
  },
  watch: {
    segments() {
      this.invalidate(true)
    },
    selectedSegments() {
      this.invalidate(true)
    },
    labels() {
      this.invalidate(false)
    },
    matrix: {
      deep: true,
      handler() {
        this.invalidate(true)
      }
    },
    showTimeLags() {
      this.invalidate(true)
    },
    linkage() {
      this.selectedLinkage = this.linkage
    }
  },
  computed: {
    brushTopLeft() {
      if (this.brushStart === null) return null
      let brushEnd = this.brushEnd;
      if (brushEnd === null) brushEnd = this.brushStart
      let fromRow = Math.min(this.brushStart[0], brushEnd[0]);
      let fromCol = Math.min(this.brushStart[1], brushEnd[1]);
      return [fromRow, fromCol]
    },
    brushBottomRight() {
      if (this.brushStart === null) return null
      let brushEnd = this.brushEnd;
      if (brushEnd === null) brushEnd = JSON.parse(JSON.stringify(this.brushStart))
      let toRow = Math.max(this.brushStart[0], brushEnd[0]);
      let toCol = Math.max(this.brushStart[1], brushEnd[1]);
      return [toRow, toCol]
    }
  },
  mounted() {
    window.addEventListener("resize", this.invalidate);
    this.selectedLinkage = this.linkage
    this.selectedThreshold = this.threshold
    this.invalidate()
    // setInterval(() => {
    //   this.time += 0.5
    // }, 500)
  },
  methods: {
    drawMatrix() {
      const ctx = this.canvas.node().getContext('2d')
      ctx.save();
      let worldWidth = this.getWorldPosition(this.dimensions[0], this.dimensions[1])
      ctx.clearRect(0, 0, worldWidth[1], worldWidth[0])
      for (let i = 0; i < this.matrix.row_segments.length; i++) {
        for (let j = 0; j < this.matrix.col_segments.length; j++) {
          let alpha = this.isSegmentSelected(i, j) ? 1. : 0.3
          ctx.fillStyle = this.addAlphaToRGBString(d3.interpolateRdBu((this.matrix.rows[i][j] + 1) / 2), alpha)
          let worldPosition = this.getWorldPosition(i, j)
          ctx.fillRect(worldPosition[1], worldPosition[0], this.rectWidth, this.rectHeight)

          if(this.showTimeLags && this.matrix.rows[i][j] != 0) {
            ctx.fillStyle = this.addAlphaToRGBString(this.$refs.transferFunction.getColor(this.matrix.time_lags[i][j]), alpha * 255)
            ctx.fillRect(worldPosition[1] + this.rectWidth / 3, worldPosition[0] + this.rectHeight / 3, this.rectWidth / 4, this.rectHeight / 4)
          }
        }
      }

      ctx.fillStyle = 'rgba(0,0,0,0.3)'
      if (this.brushTopLeft && this.brushBottomRight) {
        let wpTopLeft = this.getWorldPosition(this.brushTopLeft[0], this.brushTopLeft[1])
        let wpBottomRight = this.getWorldPosition(this.brushBottomRight[0] + 1, this.brushBottomRight[1] + 1)
        ctx.fillRect(wpTopLeft[1], wpTopLeft[0], wpBottomRight[1] - wpTopLeft[1], wpBottomRight[0] - wpTopLeft[0])
      }

      ctx.fillStyle = 'rgba(0,0,0,0.3)'
      for (let i = 0; i < this.rects.length; i++) {
        let r = this.rects[i]
        let wpTopLeft = this.getWorldPosition(r[0][0], r[0][1])
        let wpBottomRight = this.getWorldPosition(r[1][0] + 1, r[1][1] + 1)
        ctx.fillRect(wpTopLeft[1], wpTopLeft[0], wpBottomRight[1] - wpTopLeft[1], wpBottomRight[0] - wpTopLeft[0])
      }

      ctx.restore();
    },
    isSegmentSelected(row, col) {
      if (!this.hasSelection) return true
      if (this.selectedSegments[this.matrix.row_segments[row]] === true) return true
      else if (this.selectedSegments[this.matrix.col_segments[col]] === true) return true
      return false
    },
    getWorldPosition(row, col) {
      return [row * this.rectHeight, col * this.rectWidth]
    },
    getLocalPosition(x, y) {
      return [Math.floor(x / this.rectHeight), Math.floor(y / this.rectWidth)]
    },
    addAlphaToRGBString(rgbString, alpha = 1) {
      // return rgbString.replace('rgb', 'rgba')
      return rgbString.replace('rgb', 'rgba').substr(0, rgbString.length) + ', ' + alpha + ')'
    },
    invalidate(redraw = true) {
      setTimeout(() => {
        this.width = this.$refs.matrixWrapper.clientWidth - 50
        this.height = this.width * this.dimensions[1] / this.dimensions[0]
        this.rectWidth = this.width / this.dimensions[1]
        this.rectHeight = this.height / this.dimensions[0]
        this.highlightedSegmentsLocal = this.highlightedSegments
        if (redraw) {
          d3.select(this.$refs.matrixWrapper).selectAll('*').remove()
          this.canvas = d3.select(this.$refs.matrixWrapper).append('canvas')
            .attr('width', JSON.parse(JSON.stringify(this.width)))
            .attr('height', JSON.parse(JSON.stringify(this.height)))
            .on('mousemove', this.onMouseMove)
            .on('mousedown', this.onMouseDown)
            .on('mouseup', this.onMouseUp)
            .on('mouseleave', this.onMouseLeave)
          this.drawMatrix()
        }
      }, 1)

    },
    reset() {
      this.$store.dispatch('vis/loadCorrelationMatrix', {level: this.$parent.level, watershedLevel:this.$store.state.vis.overviews[this.$parent.level].segmentation.watershed_level}).then(
        response => {
          this.t += 1
        }
      ).then(
        response => this.invalidate()
      )
    },
    getColor(value, row, col) {
      let color = d3.interpolateRdYlBu(value)
      let fill = `fill: ${color};`
      let opacity = '';
      if (this.hasSelection) {
        if (!this.selectedSegments[this.matrix.row_segments[row]] && !this.selectedSegments[this.matrix.row_segments[col]]) {
          opacity = 'opacity: 0.3;'
        }
      }
      return fill + opacity;
    },
    getLabel(segment, defaultChar=null) {
      defaultChar = defaultChar || "█"
      if (!this.labels || Object.keys(this.labels).length === 0) return defaultChar
      return this.labels[segment] || defaultChar
    },
    assignLabel(segment, label) {
      this.$emit('assign-label', segment, label)
      this.resetSegementLabel()
      this.invalidate()
    },
    resetSegementLabel() {
      this.selectedSegment = null;
      this.selectedSegmentLabel = null;
      this.$emit('highlight-segment', null)
      this.$emit('set-selected-segments', [])
    },
    onMouseDown($event) {
      let mp = this.getMousePosition($event)
      let mpLocal = this.getLocalPosition(mp[0], mp[1])
      let col = mpLocal[0]
      let row = mpLocal[1]

      if ($event.shiftKey === false) {
        this.isBrushing = false;
        this.brushStart = null;
        this.brushEnd = null;
        this.$emit('set-selected-segments', [])
        this.rects = []
        this.invalidate()
        return
      }
      this.isBrushing = true
      this.brushStart = [row, col]

      if ($event.shiftKey === false) {
        this.$emit('set-selected-segments', [])
        this.rects = []
      }
    },
    onMouseMove($event) {
      let mp = this.getMousePosition($event)
      let mpLocal = this.getLocalPosition(mp[0], mp[1])
      let col = mpLocal[0]
      let row = mpLocal[1]
      let row_segment = this.matrix.row_segments[row]
      let col_segment = this.matrix.row_segments[col]
      let time_lag = this.matrix.time_lags[row][col]
      if (!this.isBrushing) {
        this.$emit('highlight-segments', [row_segment, col_segment])
      } else {
        this.brushEnd = [row, col]
        this.drawMatrix()
      }
      this.infoText = `Segments: ${this.getLabel(row_segment, row_segment)} & ${this.getLabel(col_segment, col_segment)} - Correlation certainty: ${this.matrix.rows[row][col]} -  Time lag: ${time_lag}`
    },
    onMouseUp($event) {
      if (this.isBrushing) {
        this.$emit('add-selected-segments', this.getBrushedSegments())
        this.rects.push([this.brushTopLeft, this.brushBottomRight])
        this.isBrushing = false;
        this.brushStart = null;
        this.brushEnd = null;
      }
    },
    getBrushedSegments() {
      if (this.brushTopLeft === null || this.brushBottomRight === null) return []
      let selectedRowSegments = this.matrix.row_segments.slice(this.brushTopLeft[0], this.brushBottomRight[0] + 1);
      let selectedColSegments = this.matrix.col_segments.slice(this.brushTopLeft[1], this.brushBottomRight[1] + 1);
      let selectedSegments = selectedRowSegments
      for (let j = 0; j < selectedColSegments.length; j++) {
        if (selectedSegments.indexOf(selectedColSegments[j]) >= 0) continue;
        selectedSegments.push(selectedColSegments[j])
      }
      for (let j = 0; j < this.selectedSegments.length; j++) {
        if (selectedSegments.indexOf(this.selectedSegments[j]) >= 0) continue;
        selectedSegments.push(this.selectedSegments[j])
      }
      return selectedSegments
    },
    getMousePosition($event) {
      var rect = this.canvas.node().getBoundingClientRect();
      return [Math.floor($event.clientX - rect.left), Math.ceil($event.clientY - rect.top)]
    },
    onMouseLeave() {
      this.$emit('highlight-segments', [])
      this.infoText = ''
      // this.isBrushing = false
    },
    getTextStyle(segment, type) {
      if (type === 'row') {
        if (this.selectedSegments[segment] === true) return 'fill: green; font-weight: bolder; transform: translate(-1px, 0);';
        if (this.highlightedSegments[0] === segment) return 'font-weight: bolder; transform: translate(-1px, 0);';
      } else if (type === 'column') {
        if (this.selectedSegments[segment] === true) return 'fill: green; font-weight: bolder; transform: rotate(-90deg) translate(1px, 0);';
        if (this.highlightedSegments[1] === segment) return 'font-weight: bolder; transform: rotate(-90deg) translate(1px, 0);';
      }
    },
    onResetSelection() {
      this.$emit('reset-segment-selection')
      this.rects = []
    },
    getFontColor(segment) {
      let c = this.matrix.segment_colors[segment]
      let style = `color: rgb(${c[0]}, ${c[1]}, ${c[2]});`;
      if (this.selectedSegments[segment] === true) style += 'font-weight: bolder; background-color: black;'
      if (this.highlightedSegments.indexOf(segment) >= 0) {
        if(this.selectedSegments[segment] === true) {
          style += 'text-shadow: 0 0 20px #ffffff;'
        } else {
          style += 'text-shadow: 0 0 20px #f000ff;'
        }
      }
      return style
    },
    setSelectedTimelag($event, timelag) {
      this.selectedTimeLag = timelag
      let timelags = this.$store.state.vis.overviews[this.$parent.level].correlationMatrix.matrix.time_lags
      let rows = this.$store.state.vis.overviews[this.$parent.level].correlationMatrix.matrix.rows
      let rowSegments = this.$store.state.vis.overviews[this.$parent.level].correlationMatrix.matrix.row_segments
      let colSegments = this.$store.state.vis.overviews[this.$parent.level].correlationMatrix.matrix.col_segments
      let segmentsWithThisTimelag = []
      for(let row = 0; row < timelags.length; row++) {
        for(let col = 0; col < timelags[row].length; col++) {
          if(timelags[row][col] == timelag) {
            if(rows[row][col] != 0) {
              if(segmentsWithThisTimelag.indexOf(rowSegments[row]) < 0 ) segmentsWithThisTimelag.push(rowSegments[row])
              if(segmentsWithThisTimelag.indexOf(colSegments[col]) < 0 ) segmentsWithThisTimelag.push(colSegments[col])
            }
          }
        }
      }
      this.$emit('set-selected-segments', segmentsWithThisTimelag)
    },
    correlationCertaintySelected($event, certainty) {
      certainty = certainty / 10
      console.dir($event)
      let timelags = this.$store.state.vis.overviews[this.$parent.level].correlationMatrix.matrix.time_lags
      let rows = this.$store.state.vis.overviews[this.$parent.level].correlationMatrix.matrix.rows
      let rowSegments = this.$store.state.vis.overviews[this.$parent.level].correlationMatrix.matrix.row_segments
      let colSegments = this.$store.state.vis.overviews[this.$parent.level].correlationMatrix.matrix.col_segments
      let segmentsWithCertainty = []
      for(let row = 0; row < timelags.length; row++) {
        for(let col = 0; col < timelags[row].length; col++) {
          if($event.shiftKey) {
            let r = Math.round(rows[row][col] * 10) / 10
            if(r == certainty) {
              if(segmentsWithCertainty.indexOf(rowSegments[row]) < 0 ) segmentsWithCertainty.push(rowSegments[row])
              if(segmentsWithCertainty.indexOf(colSegments[col]) < 0 ) segmentsWithCertainty.push(colSegments[col])
            }
          } else {
            if(certainty < 0) {
              if(rows[row][col] <= certainty) {
                if(segmentsWithCertainty.indexOf(rowSegments[row]) < 0 ) segmentsWithCertainty.push(rowSegments[row])
                if(segmentsWithCertainty.indexOf(colSegments[col]) < 0 ) segmentsWithCertainty.push(colSegments[col])
              }
            }
            if(certainty >= 0) {
              if(rows[row][col] >= certainty) {
                if(segmentsWithCertainty.indexOf(rowSegments[row]) < 0 ) segmentsWithCertainty.push(rowSegments[row])
                if(segmentsWithCertainty.indexOf(colSegments[col]) < 0 ) segmentsWithCertainty.push(colSegments[col])
              }
            }
          }
        }
      }
      console.log(segmentsWithCertainty)
      this.$emit('set-selected-segments', segmentsWithCertainty)
    }
  }
}
</script>
