<template>
  <div class="container-fluid" style="max-width: 3340px">
<!--    {{overviews[0]}}-->
    <ul class="nav nav-tabs mb-2">
      <li class="nav-item"  v-for="(overview, level) in overviews" :key="level" v-show="overview.isActive !== false">
        <a class="nav-link " :class="{active: level == activeOverviewTab}"><a class="btn btn-sm" @click="$store.dispatch('vis/setOverviewTab', level)" >Overview Level {{level}}</a> <a class="btn btn-sm btn-outline-danger" style="border: none;" @click="$store.dispatch('vis/removeOverview', level)">x</a></a>
      </li>
    </ul>

<!--    <pre v-for="(overview, level) in overviews">{{overview}}</pre>-->
    <ensemble-overview
      :overview="overview"
      :level="level"
      v-for="(overview, level) in overviews"
      :key="level"
      v-show="level == activeOverviewTab && overview.isActive !== false"

    ></ensemble-overview>

  </div>
</template>

<script>
import EnsembleOverview from "../components/EnsembleOverview";
export default {
  components: {EnsembleOverview},
  computed: {
    overviews() {
      return this.$store.state.vis.overviews
    },
    activeOverviewTab() {
      return this.$store.state.vis.activeOverviewTab
    }
  },
  created() {
    this.$store.dispatch('vis/timeLagRange')
    this.$store.dispatch('vis/fetchThresholds')
  }
}
</script>
