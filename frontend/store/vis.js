import Vue from 'vue'

const BACKEND_URL = 'http://127.0.0.1:5000'


function unique(arr) {
  var u = {}, a = [];
  for(var i = 0, l = arr.length; i < l; ++i){
    if(!u.hasOwnProperty(arr[i])) {
      a.push(arr[i]);
      u[arr[i]] = 1;
    }
  }
  return a;
}

export const state = () => ({
  history: [],
  thresholds: [],
  watershed_level: process.env.initWatershedLevel,
  overviews: {
    "1": {
      isActive: true,
      segmentation: {},
      correlationMatrix: {},
      selectedSegments: {},
      filteredSegments: {},
      labels: {},
      refined: []
    }
  },
  details: [],
  mdsImage: null,
  activeOverviewTab: "1",
  t: 0,
  overlay: null,
  timeLagRange: [0, 1],
  swapHalf: false
})

export const actions = {
  resetSegmentSelection({state, commit, dispatch}, {level, segment}) {
    commit('updateOverview', {level, key: 'selectedSegments', value: {}})
    if(process.env.onTheFlyDetails) dispatch('fetchDetails', level)
  },
  setSelectedSegments({state, commit, dispatch}, {level, segments}) {
    commit('updateOverview', {level, key: 'selectedSegments', value: Object.assign({}, ...segments.map((s) => ({[s]: true})))})
    if(process.env.onTheFlyDetails) dispatch('fetchDetails', level)
  },
  addSelectedSegment({state, commit, dispatch}, {level, segment}) {
    let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegments))
    selectedSegments[segment] = true
    commit('updateOverview', {level, key: 'selectedSegments', value: selectedSegments})
    if(process.env.onTheFlyDetails) dispatch('fetchDetails', level)
  },
  addSelectedSegments({state, commit, dispatch}, {level, segments}) {
    let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegments))
    for(let s in segments) {
      selectedSegments[segments[s]] = true
    }
    commit('updateOverview', {level, key: 'selectedSegments', value: selectedSegments})
    if(process.env.onTheFlyDetails) dispatch('fetchDetails', level)
  },
  removeSelectedSegment({state, commit, dispatch}, {level, segment}) {
    let selectedSegments = JSON.parse(JSON.stringify(state.overviews[level].selectedSegments))
    delete selectedSegments[segment]
    commit('updateOverview', {level, key: 'selectedSegments', value: selectedSegments})
    if(process.env.onTheFlyDetails) dispatch('fetchDetails', level)
  },
  assignSegmentLabel({state, commit}, {level, segment, label}) {
    let labels = JSON.parse(JSON.stringify(state.overviews[level].labels))
    labels[segment] = label
    commit('updateOverview', {level, key: 'labels', value: labels})
  },
  filterSelection({state, commit}, {level}) {
    let newOverview = JSON.parse(JSON.stringify(state.overviews[level]))
    newOverview.filteredSegments = {}
    for(let s in state.overviews[level].selectedSegments) {
      newOverview.filteredSegments[s] = true
    }
    let highestLevel = Math.max(...Object.keys(state.overviews).map(k => parseInt(k)))
    newOverview.level = parseInt(highestLevel) + 1
    newOverview.selectedSegments = {}
    newOverview.segmentation.segments = newOverview.segmentation.segments.concat(state.overviews[level].refined)
    commit('createOverview', {level: newOverview.level, newOverview})

    return newOverview

  },
  setOverviewTab({state, commit}, level) {
    commit('activeOverviewTab', level)
  },
  removeOverview({state, commit}, level) {
    let confi = confirm('Do you really want to close this view?')
    if(!confi) return
    let o = JSON.parse(JSON.stringify(state.overviews))
    delete o[level]
    commit('overviews', o)
    commit('activeOverviewTab', parseInt(level) - 1)
  },
  loadSegmentation({state, commit}, {level, watershedLevel}) {
    return this.$axios.get(BACKEND_URL + '/get-segments-by-watershed-level/' + watershedLevel).then(
      response => {
        commit('updateOverview', {level, key: 'segmentation', value: response.data})

      }
    )
  },
  loadCorrelationMatrix({state, commit}, {level, watershedLevel, segments}) {
    let link = state.overviews[level].correlationMatrix.linkage ? state.overviews[level].correlationMatrix.linkage : process.env.defaultLinkage
    let threshold = state.overviews[level].correlationMatrix.threshold ? state.overviews[level].correlationMatrix.threshold : process.env.defaultThreshold
    let url = `${BACKEND_URL}/get-correlation-matrix-by-watershed-level/${watershedLevel}/${threshold}/${link}`

    let loadedSegments = state.overviews[level].segmentation.segments ? state.overviews[level].segmentation.segments.map(s => s.segment) : []
    let refinedSegments = state.overviews[level].refined.map( r => r.segment )
    let s = loadedSegments.concat(refinedSegments)
    if(Object.keys(state.overviews[level].filteredSegments).length > 0) {
      s = Object.keys(state.overviews[level].filteredSegments)
    }
    if (segments) {
      s = segments
    }

    // s = unique(s)

    // let s = segments ? segments : state.overviews[level].segmentation.segments.map(s => s.segment).concat()
    // if (!segments && Object.keys(state.overviews[level].filteredSegments).length > 0) {
    // }

    if(s.length > 0) url += `/${s.join(',')}`


    return this.$axios.get(url).then(
      response => {
        if(response.data === null) {
          return
        }
        commit('updateOverview', {level, key: 'correlationMatrix', value: response.data})
      }
    )
  },
  changeCorrelationMatrixLinkage({state, commit, dispatch}, {level, linkage}) {
    let correlationMatrix = JSON.parse(JSON.stringify(state.overviews[level].correlationMatrix))
    correlationMatrix.linkage = linkage
    commit('updateOverview', {level, key: 'correlationMatrix', value: correlationMatrix})

    return linkage
  },
  changeCorrelationMatrixThreshold({state, commit, dispatch}, {level, threshold}) {
    let correlationMatrix = JSON.parse(JSON.stringify(state.overviews[level].correlationMatrix))
    correlationMatrix.threshold = threshold
    commit('updateOverview', {level, key: 'correlationMatrix', value: correlationMatrix})

    return threshold
  },
  refineSegments({state, commit, dispatch}, {level, segments, initWatershedLevel, watershedLevel}) {
    this.$axios.get(`${BACKEND_URL}/refine-segment/${Object.keys(segments).join(',')}/${initWatershedLevel}/${watershedLevel}`).then(
      response => {

        let segmentation = JSON.parse(JSON.stringify(state.overviews[level].segmentation))

        let newSegments = response.data.segments

        segmentation.segments = state.overviews[level].segmentation.segments.filter(s => !segments[s.segment])
        let filtered = JSON.parse(JSON.stringify(state.overviews[level].filteredSegments))
        for(let i = 0; i < newSegments.length; i++) {
          filtered[newSegments[i].segment] = true
          let s = newSegments[i]
          let ss = state.overviews[level].segmentation.segments.filter(sss => sss.segment === s.segment)
          if(ss.length > 0) continue
          segmentation.segments.push(s)
        }
        if(Object.keys(state.overviews[level].filteredSegments).length > 0)
          commit('updateOverview', {level, key: 'filteredSegments', value:filtered})
        commit('updateOverview', {level, key: 'segmentation', value: segmentation})
        commit('updateOverview', {level, key: 'refined', value: state.overviews[level].refined.concat(newSegments)})

        let allSegments = []
        if(Object.keys(state.overviews[level].filteredSegments).length > 0) {
          for(let segment in state.overviews[level].filteredSegments) {
            if(!segments || !segments[segment])
              allSegments.push(segment)
          }
        } else {
          allSegments = segmentation.segments.map(s => s.segment)
        }
        dispatch('loadCorrelationMatrix', {
          level, watershedLevel,
          segments: allSegments
        })

        dispatch('setSelectedSegments', {level, segments: newSegments.map(s => s.segment)})

        commit('pushHistory')

        return segmentation

      }
    )
  },
  undo({state, commit}) {
    if(state.history.length === 0) return

    let nextState = state.history[state.history.length - 1]
    // if(Object.keys(nextState[0].segmentation).length === 0) return
    let overviews = JSON.parse(JSON.stringify(nextState))
    commit('undo', overviews)
  },
  fetchThresholds({state, commit}) {
    this.$axios.get(BACKEND_URL + '/get-thresholds').then(
      response => {
        commit('thresholds', response.data)
      }
    )
  },
  fetchDetails({state, commit}, level) {
    let segments = Object.keys(state.overviews[level].selectedSegments)
    segments = unique(segments)
    if(segments.length === 0) return commit('details', {})
    this.$axios.get(BACKEND_URL + '/get-curves-for-segments/' + segments.join(',')).then(
      response => {
        commit('details', response.data)
      }
    )

  },
  getMdsImage({state, commit}) {
    this.$axios(BACKEND_URL + '/get-mds-image/' +  state.swapHalf).then(
      response => {
        commit('mdsImage', response.data.image)
        commit('overlay', response.data.overlay)
      }
    )
  },
  timeLagRange({state, commit}) {
    this.$axios.get(BACKEND_URL + '/get-time-lag-range').then(
      response => {
        commit('timeLagRange', response.data)
      }
    )
  },
  swapHalf({state, commit, dispatch}, swapHalf) {
    commit('swapHalf', swapHalf)
    dispatch('getMdsImage')
  }
}

export const mutations = {
  overviews(state, overviews) {
    state.history.push(state.overviews)
    state.overviews = overviews;
    state.t += 1
  },
  thresholds(state, thresholds) {
    state.thresholds = thresholds;
    state.t += 1
  },
  undo(state, overviews) {
    state.overviews = overviews;
    state.history.pop()
    state.t += 1
  },
  activeOverviewTab(state, activeOverviewTab) {
    state.activeOverviewTab = activeOverviewTab
    state.t += 1
  },
  updateOverview(state, {level, key, value}) {
    Vue.set(state.overviews[level], key, value)
    state.t += 1

  },
  pushHistory(state) {
    state.history.push(state.overviews)
    state.t += 1
  },
  removeOverview(state, level) {
    state.overviews[level].isActive = false
    state.t += 1
  },
  createOverview(state, {level, newOverview}) {
    state.overviews[level] = newOverview
    state.activeOverviewTab = level
    state.t += 1
  },
  hideOverview(state, level) {
    state.overviews[level].isActive = false
    state.t += 1
  },
  details(state, details) {
    state.details = details
  },
  mdsImage(state, mdsImage) {
    state.mdsImage = mdsImage
  },
  timeLagRange(state, range) {
    state.timeLagRange = range
  },
  swapHalf(state, swapHalf) {
    state.swapHalf = swapHalf
  },
  overlay(state, overlay) {
    state.overlay = overlay
  }
}
