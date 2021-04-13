<template>
  <div class="card" style="user-select: none;">
    <h5 class="card-header">Similarity Image
      <span class="float-right"><small><a @click="show = !show"><span v-if="show">hide</span><span v-else>show</span></a></small></span>
    </h5>
    <div class="card-body" v-show="show">
<!--      <label><input type="checkbox" v-model="swap"> Swap half width</label>-->
      <label v-if="$store.state.vis.overlay"><input type="checkbox" v-model="showOverlay"> Show overlay</label>
      <div style="position: relative">
        <img :src="'data:image/png;base64,' + $store.state.vis.mdsImage" style="width: 100%" :style="isRotated ? 'transform:rotate(180deg) scaleX(-1)' : null">
        <img :src="'data:image/png;base64,' + $store.state.vis.overlay" style="width: 100%; position: absolute; height: 79.3%; left:0 ; top: 2.6%; right: 0.1%" :style="!isRotated ? 'transform:rotate(180deg) scaleX(-1)' : null" v-if="showOverlay">
      </div>

    </div>
  </div>
</template>

<script>
export default {
  components: {},
  computed: {
    isRotated() {
      return process.env.isRotated
    },
    swap: {
      get() { return this.$store.state.vis.swapHalf },
      set(swapHalf) { this.$store.dispatch('vis/swapHalf', swapHalf) }
    }
  },
  watch: {
  },
  data() {
    return {
      showOverlay: false,
      show: true
    }
  },
  created() {
  },
  mounted() {
  },
  methods: {
  }
}
</script>
