<template>
  <div class="row">
    <div class="col-sm-12 pb-2">
      <div class="btn-group" style="float: right;">
        <a class="btn btn-info" @click="$store.dispatch('vis/undo')" :disabled="overview.segmentation === null">undo</a>
      </div>
    </div>
    <div class="col-sm-6">
      <image-view></image-view>
      <div class="mt-2"></div>

      <segmentation-view
        v-if="overview.segmentation.segments"
        :segments="overview.segmentation.segments"
        :dimensions="overview.segmentation.dimensions"
        :selected-segments="overview.selectedSegments"
        :filtered-segments="overview.filteredSegments"
        :highlighted-segments="highlightedSegments"
        :labels="labels"
        :init-watershed-level="initWatershedLevel"
        @reset-segment-selection="resetSegmentSelection"
        @add-selected-segment="addSelectedSegment"
        @remove-segment-selection="removeSegmentSelection"
        @assign-label="assignSegmentLabel"
        @highlight-segments="highlightSegments"
        @filter-selection="filterSelection"
        @load-segmentation="loadSegmentation"
        @refine-segments="refineSegments"
        :t="overview.t"

      ></segmentation-view>

    </div>
    <div class="col-sm-6">
      <matrix-view
        ref="matrixView"
        v-if="overview.correlationMatrix.matrix"
        :matrix="overview.correlationMatrix.matrix"
        :dimensions="overview.correlationMatrix.dimensions"
        :selected-segments="overview.selectedSegments"
        :filtered-segments="overview.filteredSegments"
        :highlighted-segments="highlightedSegments"
        :linkage="overview.correlationMatrix.linkage"
        :labels="labels"
        :t="t"
        @assign-label="assignSegmentLabel"
        @highlight-segments="highlightSegments"
        @set-selected-segments="setSelectedSegments"
        @add-selected-segments="addSelectedSegments"
        @reset-segment-selection="resetSegmentSelection"
        @filter-selection="filterSelection"
        @change-linkage="changeCorrelationMatrixLinkage"
        @change-threshold="changeCorrelationMatrixThreshold"
      ></matrix-view>
      <div class="mt-2"></div>
      <detail-view
        :labels="labels"
        @highlight-segments="highlightSegments"
      ></detail-view>
    </div>
    <div class="col-sm-6">

    </div>
  </div>
</template>

<script>
import SegmentationView from "./SegmentationView";
import MatrixView from "./MatrixView";
import DetailView from "./DetailView";
import ImageView from "./ImageView";

export default {
  components: {ImageView, DetailView, MatrixView, SegmentationView},
  props: {
    overview: {type: Object},
    level: {}
  },
  data() {
    return {
      highlightedSegments: [],
      t: 0,
      initWatershedLevel: process.env.initWatershedLevel
    }
  },
  computed: {
    labels() {
      return this.overview.labels
    },
    hasSelection() {
      return Object.keys(this.overview.selectedSegments).length > 0
    }
  },
  mounted() {
    if(Object.keys(this.overview.segmentation).length === 0)
      this.loadSegmentation(this.initWatershedLevel)
    if(Object.keys(this.overview.segmentation).length !== 0) {
      this.initWatershedLevel = this.overview.segmentation.watershed_level
    }
    this.loadCorrelationMatrix(this.initWatershedLevel)

    this.$store.dispatch('vis/getMdsImage')
  },
  methods: {
    resetSegmentSelection() {
      this.$store.dispatch('vis/resetSegmentSelection', {
        level: this.level
      })
    },
    addSelectedSegment(segment) {
      this.$store.dispatch('vis/addSelectedSegment', {
        level: this.level,
        segment: segment
      })
    },
    addSelectedSegments(segments) {
      this.$store.dispatch('vis/addSelectedSegments', {
        level: this.level,
        segments: segments
      })
    },
    removeSegmentSelection(segment) {
      this.$store.dispatch('vis/removeSelectedSegment', {
        level: this.level,
        segment: segment
      })
    },
    assignSegmentLabel(segment, label) {
      if (segment === null) return alert('Error: No segment selected.')
      if (label === null || label === '') label = null
      this.$store.dispatch('vis/assignSegmentLabel', {
        level: this.level,
        segment: segment,
        label: label
      })
      setTimeout(() => {
        this.$forceUpdate()

      }, 1000)
    },
    highlightSegments(segments) {
      if(!segments) segments = []
      this.highlightedSegments = segments
    },
    setSelectedSegments(segments) {
      this.$store.dispatch('vis/setSelectedSegments', {
        level: this.level,
        segments: segments
      })
    },
    filterSelection() {
      this.$store.dispatch('vis/filterSelection', {
        level: this.level
      })
    },
    loadSegmentation(watershedLevel) {
      this.$store.dispatch('vis/loadSegmentation', {level: this.level, watershedLevel:watershedLevel}).then(
        response => {
        }
      ).then(
        response => {
          this.loadCorrelationMatrix(watershedLevel)
        }
      )
    },
    loadCorrelationMatrix(watershedLevel) {
      this.$store.dispatch('vis/loadCorrelationMatrix', {level: this.level, watershedLevel: watershedLevel}).then(
        response => {
          this.t += 1
          console.log('correlation matrix loaded')
        }
      )
    },
    changeCorrelationMatrixLinkage(linkage) {
      console.log('set linkage ', linkage)
      this.$store.dispatch('vis/changeCorrelationMatrixLinkage', {level: this.level, linkage:linkage}).then(
        response => {
          this.loadCorrelationMatrix(this.overview.segmentation.watershed_level)
        }
      )
    },
    changeCorrelationMatrixThreshold(threshold) {
      this.$store.dispatch('vis/changeCorrelationMatrixThreshold', {level: this.level, threshold:threshold}).then(
        response => {
          this.loadCorrelationMatrix(this.overview.segmentation.watershed_level)
        }
      )
    },
    refineSegments({initWatershedLevel, segments, watershedLevel}) {
      this.$store.dispatch('vis/refineSegments', {
        level: this.level,
        initWatershedLevel: initWatershedLevel,
        segments: segments,
        watershedLevel: watershedLevel
      }).then(
        this.t += 1
      )
    }
  }
}
</script>
