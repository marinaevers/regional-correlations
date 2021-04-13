<template>
  <div class="row"  @mouseleave="hoveredValue = null">
    <div class="col-sm-11">
      <div>
        <div class="text-center" v-if="title">{{title}}</div>
        <div @mouseover="hoveredValue = r" @click="$emit('value-selected', $event, r)" v-for="r in range" :style="`float:left;width:${width}%;background-color:${getColor(r)};text-align:center;font-size:0.8rem;`">
          <!--      {{r}}-->
          &nbsp;
        </div>
        <div class="row">
          <div class="col-sm-4">
            <span v-if="labels.length == 3">{{labels[0]}}</span>
            <span v-else>{{domainFrom}}</span>
          </div>
          <div class="col-sm-4 text-center">
            <span v-if="labels.length == 3">{{labels[1]}}</span>
            <span v-else>{{domainTo + domainFrom}}</span>

          </div>
          <div class="col-sm-4 text-right">
            <span v-if="labels.length == 3">{{labels[2]}}</span>
            <span v-else>{{domainTo}}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="col-sm-1">
      {{hoveredValue}}
    </div>
  </div>
</template>

<script>
import * as d3 from "d3";

export default {
  components: {},
  props: {
    domainFrom: {},
    domainTo: {},
    transferFunction: {},
    labels: { default: () => []},
    title: { default: null},
  },
  computed: {
    range() {
      let range = []
      for (let i = this.domainFrom; i <= this.domainTo; i++) {
        range.push(i)
      }
      return range
    },
    width() {
      return 100 / this.range.length
    }
  },
  data() {
    return {
      hoveredValue: null
    }
  },
  created() {
  },
  mounted() {
  },
  methods: {
    getColor(r) {
      return d3[this.transferFunction]((r - this.domainFrom) / (this.domainTo - this.domainFrom))
    }
  }
}
</script>
