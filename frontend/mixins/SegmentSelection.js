export default {
  props: {
    selectedSegments: {
      type: Object, default: () => {
      }
    }
  },
  computed: {
    hasSelection() {
      if(!this.selectedSegments) return false
      return Object.keys(this.selectedSegments).length > 0
    }
  }
}
