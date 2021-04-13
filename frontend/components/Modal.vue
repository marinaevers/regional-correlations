<template>
  <div class="modal fade show" aria-modal="true" role="dialog" tabindex="-1" style="display: block">
    <div class="backdrop" style="position: absolute; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5);" @click="close"></div>
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title"><slot name="title"></slot></h5>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close" @click="close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body" style="max-height: 80vh; overflow-y: auto">
          <slot name="body"></slot>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal" @click="close">Close</button>
          <button type="button" class="btn btn-primary" @click="okay">Okay</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  components: {},
  props: {
    onOkayClicked: {type: Function},
  },
  data() {
    return {}
  },
  created() {
  },
  mounted() {
    window.addEventListener("keyup", (event) => {
      if (event.key === 'Enter') {
        this.$emit('okay')
      }
      else if(event.key === 'Escape') {
        this.$emit('close')
      }
    });
  },
  methods: {
    okay() {
      this.$emit('okay')
    },
    close() {
      this.$emit('close')
    }
  }
}
</script>
