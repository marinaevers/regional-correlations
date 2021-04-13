export default {
  props: {
    filteredSegments: {
      type: Object, default: () => {
      }
    },
  },
  computed: {
    isFiltered() {
      if (Object.keys(this.filteredSegments).length === 0) return false
      for (let k in this.filteredSegments) {
        if (this.filteredSegments[k] === true) return true
      }
      return false
    }
  }
}
