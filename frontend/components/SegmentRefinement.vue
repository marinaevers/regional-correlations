<template>
  <div class="form-group">
    <label for="formControlRange">Refinement watershed level ({{watershedLevel}})</label>
    <input type="range" class="form-control-range" id="formControlRange" v-model="watershedLevel" @change="refine" :max="initWatershedLevel">
  </div>
</template>

<script>
export default {
  components: {},
  props: {
    segments: {
      default: () => []
    },
    initWatershedLevel: {
      default: 5
    }
  },
  data() {
    return {
      watershedLevel: null
    }
  },
  computed: {
  },
  mounted() {
    this.watershedLevel = this.initWatershedLevel
  },
  methods: {
    refine() {
      this.$emit('refine-segments', {
        initWatershedLevel: this.initWatershedLevel,
        segments: this.segments,
        watershedLevel: this.watershedLevel
      })
    }
  }
}
</script>
