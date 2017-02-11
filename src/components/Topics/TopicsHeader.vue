<template>
  <div>
    <md-layout md-row md-gutter="24" class="mt-topics-header">
      <md-layout md-flex>
        <md-input-container>
          <label>Filter</label>
          <md-input @change='filterUpdated'/>
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
import types from '../../store/types'
import { mapState } from 'vuex'

export default {
  computed: mapState({
    order: state => state.topics.order
  }),
  name: 'TopicsHeader',
  methods: {
    filterUpdated (value) {
      this.$store.commit(types.SET_FILTER_STRING, { value })
    },

    setOrder (order) {
      this.$store.commit(types.SET_ORDER, { order })
    }
  }
}
</script>

<style scoped>
.mt-topics-header {
  padding: 0px 16px;
}
</style>
