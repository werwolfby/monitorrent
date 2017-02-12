<template>
  <div>
    <md-layout md-row md-gutter="24" class="mt-topics-header">
      <md-layout md-flex>
        <md-input-container>
          <label>Filter</label>
          <md-input :value='filter' @change='setFilter'/>
        </md-input-container>
      </md-layout>

      <div>
        <md-input-container>
          <label>Sort</label>
          <md-select :value="order" @selected="setOrder">
            <md-option value="display_name">Name</md-option>
            <md-option value="-last_update">Last Update</md-option>
          </md-select>
        </md-input-container>
      </div>

      <md-button class="md-icon-button" style="margin: auto 12px">
        <md-icon>add</md-icon>
      </md-button>
    </md-layout>
    <md-divider></md-divider>
  </div>
</template>

<script>
export default {
  props: ['filter', 'order'],
  name: 'TopicsHeader',
  methods: {
    setFilter (value) {
      this.$emit('change-filter', value)
    },

    setOrder (order) {
      this.$emit('change-order', order)
    }
  }
}
</script>

<style scoped>
.mt-topics-header {
  padding: 0px 16px;
}
</style>
