<template>
  <div class="card" style="user-select: none;">
    <h5 class="card-header"><a @click="invalidate">Segmentation View</a>
      <span class="float-right"><small><a @click="show = !show"><span v-if="show">hide</span><span
        v-else>show</span></a></small></span>
    </h5>
    <div class="card-body" v-show="show">
      <span v-show="false">{{ t }}</span>
      <div class="row">
        <div class="col-sm-5">
          <div class="row">
            <div class="col-sm-9">
              <div class="form-group">

                <label for="formControlRange">Watershed level ({{ watershedLevel }})</label>

                <input type="range" class="form-control-range" id="formControlRange" v-model="watershedLevel"
                       @change="$emit('load-segmentation', $event.target.value)" :max="1000">
              </div>

            </div>
            <div class="col-sm-3">
              <input v-model="watershedLevel" @change="$emit('load-segmentation', $event.target.value)"
                     class="form-control">
            </div>
          </div>
        </div>
        <div class="col-sm-5">
          <segment-refinement
            v-show="hasSelection"
            :segments="selectedSegments"
            :init-watershed-level="watershedLevel"
            @refine-segments="$emit('refine-segments', $event)"
          ></segment-refinement>
        </div>
        <div class="col-sm-2 text-right">{{segmentCount}} segments</div>
      </div>

      <div ref="segmentCanvasWrapper">
        <svg :width="width" :height="height" :viewBox="`0 0 ${dimensions[0]} ${dimensions[1]} `"
             @mouseleave="$emit('highlight-segments', [])"
          :style="isRotated ? 'transform:rotate(180deg) scaleX(-1)' : null"
        >
          <polygon v-for="segment in polygons"
                   :points="polygonPointString(segment.hull)"
                   :style="getSegmentColor(segment)"
                   @click="onSegmentClicked($event, segment.segment)"
                   @mouseover="onSegmentMouseOver($event, segment.segment)"
          ></polygon>
          <line v-for="segment in pixels"
                :x1="segment.hull[0][0]"
                :x2="segment.hull[segment.hull.length - 1][0]"
                :y1="segment.hull[0][1]"
                :y2="segment.hull[segment.hull.length - 1][1]"
                :style="getSegmentColor(segment, true)"
                @click="onSegmentClicked($event, segment.segment)"
                @mouseover="onSegmentMouseOver($event, segment.segment)"
          ></line>
        </svg>

        <segment-label-modal
          @close="resetSegementLabel"
          @okay="assignLabel"
          v-if="selectedSegment !== null"
          :selected-segment="selectedSegment"
          :selected-segment-label="selectedSegmentLabel"
        ></segment-label-modal>

        <modal v-if="showSegmentTable" @close="showSegmentTable = null" @okay="showSegmentTable = null">
          <div slot="body">
            <table class="table">
              <tr>
                <th style="width: 50px;">Segment</th>
                <th>Label <small><a @click="tableLabeledOnly = !tableLabeledOnly">only</a></small></th>
                <th>&nbsp;</th>
              </tr>
              <tr v-for="segment in segments"
                  v-if="!tableLabeledOnly || labels[segment.segment] !== undefined"
                  :class="{'table-secondary': selectedSegments[segment.segment] === true}"
                  @mouseover="$emit('highlight-segments', [segment.segment])"
                  @mouseleave="$emit('highlight-segments', [])">
                <td>{{ segment.segment }}</td>
                <td>
                  <input class="form-control" :value="labels[segment.segment]"
                         @input="assignLabel(segment.segment, $event.target.value )">
                </td>
                <td class="text-right">
                  <a v-if="selectedSegments[segment.segment] !== true" class="btn btn-success btn-sm"
                     @click="$emit('add-selected-segment', segment.segment)">select</a>
                  <a v-else class="btn btn-danger btn-sm" @click="$emit('remove-segment-selection', segment.segment)">unselect</a>
                </td>
              </tr>
            </table>
          </div>
        </modal>
      </div>
    </div>
    <div class="card-footer" v-show="show">
      <div class="row">
        <div class="col-sm-3">
          {{ hoverLabel }} Min:{{ hoverMin }}, Max:{{ hoverMax }}
        </div>
        <div class="col-sm-9">
          <div class="text-right">
            <div class="btn-group">
              <a class="btn btn-sm btn-secondary" @click="$emit('reset-segment-selection')"
                 v-if="hasSelection">Reset selection</a>
              <a class="btn btn-sm btn-info" @click="$emit('filter-selection')" v-if="hasSelection">Filter selection</a>
              <a class="btn btn-sm btn-success" @click="showSegmentTable = !showSegmentTable">Show table</a>
            </div>
          </div>
        </div>
      </div>

    </div>

  </div>
</template>

<script>
import * as d3 from "d3";
import Modal from "./Modal";
import SegmentLabelModal from "./SegmentLabelModal";
import SegmentFilter from "@/mixins/SegmentFilter";
import SegmentSelection from "@/mixins/SegmentSelection";
import SegmentRefinement from "./SegmentRefinement";

export default {
  components: {SegmentRefinement, SegmentLabelModal, Modal},
  props: {
    segments: {type: Array, default: () => []},
    dimensions: {type: Array, default: () => [100, 100]},
    highlightedSegments: {type: Array, default: () => []},
    labels: {
      type: Object, default: () => {
        return {}
      }
    },
    initWatershedLevel: {},
    t: {}
  },
  mixins: [SegmentFilter, SegmentSelection],
  data() {
    return {
      show: true,
      width: null,
      height: null,
      selectedSegment: null,
      selectedSegmentLabel: null,
      showSegmentTable: false,
      hoverLabel: null,
      hoverMin: null,
      hoverMax: null,
      tableLabeledOnly: false,
      clicks: 0,
      timer: null,
      watershedLevel: process.env.initWatershedLevel
    }
  },
  computed: {
    polygons() {
      let polygons = []
      for (let i = 0; i < this.segments.length; i++) {
        let segment = this.segments[i];
        if (segment.is_line === false) {
          polygons.push(segment)
        }
      }
      return polygons
    },
    isRotated() {
      return process.env.isRotated
    },
    pixels() {
      let pixels = []
      for (let i = 0; i < this.segments.length; i++) {
        let segment = this.segments[i];
        if (segment.is_line === true) {
          pixels.push(segment)
        }
      }
      return pixels
    },
    segmentCount() {
      let loadedSegments = this.segments.map(s => s.segment)
      let ssss = this.unique(loadedSegments)
      console.log('component', ssss.length)
      return ssss.length
    }
  },
  watch: {
    segments() {
      this.invalidate()
    },
    selectedSegments() {
      this.invalidate()
    },
    highlightedSegments() {
      this.invalidate()
    },
    labels() {
      this.invalidate()
    }
  },
  mounted() {
    window.addEventListener("resize", this.invalidate);
    this.invalidate()
  },
  methods: {
    invalidate() {
      this.width = this.$refs.segmentCanvasWrapper.clientWidth
      this.height = this.width * this.dimensions[1] / this.dimensions[0]
    },
    polygonPointString(segmentHull) {
      return segmentHull.map((d) => {
        return [d[1], d[0]]
      }).join(' ')
    },
    getSegmentColor(segment, withStroke = false) {
      let color = `rgba(${segment.color[0]},${segment.color[1]},${segment.color[2]},${segment.color[3]});`
      if (Object.keys(this.filteredSegments).length > 0 && this.filteredSegments[segment.segment] !== true) color = 'rgba(0,0,0,0.02)'
      let fill = `fill: ${color};`
      if (this.hasSelection && !this.selectedSegments[segment.segment])
        fill = `fill: ${color}; opacity: 0.05;`
      let stroke = this.labels[segment.segment] ? 'stroke: black; stroke-width: 0.5px; stroke-dasharray:2,0.5;' : ''
      if (this.highlightedSegments !== null && this.highlightedSegments.indexOf(segment.segment) >= 0) {
        stroke = 'stroke: #f000ff; stroke-width: 1px;'
      } else {
        if (withStroke) {
          stroke = `stroke: ${color}; stroke-width: 0.5px;`
        }
      }
      return fill + stroke

    },
    onSegmentClicked(e, segment) {
      this.clicks++
      if (this.clicks === 1) {
        this.timer = setTimeout(() => {
          this.onSegmentSingleClicked(e, segment)
          this.clicks = 0
        }, 200);
      } else {
        clearTimeout(this.timer);
        this.onSegmentDoubleClicked(e, segment)
        this.clicks = 0;
      }
    },
    onSegmentSingleClicked(e, segment) {
      if (this.selectedSegments[segment] === true) { // if already selected, unselect
        if (e.shiftKey) {
          this.$emit('remove-segment-selection', segment)
        }
      } else {
        if (e.shiftKey) {
          this.$emit('add-selected-segment', segment)
        }
      }
    },
    onSegmentDoubleClicked(e, segment) {
      this.selectedSegment = segment;
      this.selectedSegmentLabel = this.labels[segment] || null;
    },
    assignLabel(segment, label) {
      // if (segment === null || label === null || label === '') return alert('Error: Label missing.')
      this.$emit('assign-label', segment, label)
      this.resetSegementLabel()
      this.invalidate()
    },
    resetSegementLabel() {
      this.selectedSegment = null;
      this.selectedSegmentLabel = null;
      this.$emit('highlight-segments', [])
    },
    onSegmentMouseOver(e, segment) {
      this.hoverLabel = this.labels[segment] || segment;
      for (let i = 0; i < this.segments.length; i++) {
        if (this.segments[i].segment === segment) {
            this.hoverMin = this.segments[i].min;
            this.hoverMax = this.segments[i].max;
          break;
        }
      }
      this.$emit('highlight-segments', [segment])
    },
    filter() {

    },
    unique(arr) {
      var u = {}, a = [];
      for(var i = 0, l = arr.length; i < l; ++i){
        if(!u.hasOwnProperty(arr[i])) {
          a.push(arr[i]);
          u[arr[i].segment] = 1;
        }
      }
      return a;
    }
  }
}
</script>
