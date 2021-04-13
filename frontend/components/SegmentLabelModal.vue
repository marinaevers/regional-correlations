<template>
  <modal @close="$emit('close')" @okay="$emit('okay', selectedSegment, label)">
    <span slot="title" class="no-selection">Segment label</span>
    <div slot="body">
      <div class="form-group no-selection">
        <label>Assign label for segment <i>{{ selectedSegment }}</i> <small v-if="label !== null">({{label}})</small></label>
        <input type="text" class="form-control" placeholder="Segment label" v-model="label" v-cloak>
      </div>
    </div>
  </modal>
</template>

<script>
export default {
  components: {},
  props: {
    selectedSegment: {},
    selectedSegmentLabel: {}
  },
  data() {
    return {
      label: null
    }
  },
  watch: {
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
  created() {
    this.label = this.selectedSegmentLabel
  },
  mounted() {
  },
  methods: {}
}
</script>
