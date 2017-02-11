<template>
  <div :class="{ 'color-failed': execute && execute.failed > 0, 'color-downloaded': execute && execute.failed == 0 && execute.downloaded > 0 }">
    <md-layout md-row md-gutter="24" class="mt-topics-header" v-if='loading'>
      <md-layout md-flex>
        <h4 md-flex class="mt-subheader mt-executing">
          <span class="mt-bold">Updating torrents...</span>
        </h4>
      </md-layout>
    </md-layout>
    <md-layout md-row md-gutter="24" class="mt-topics-header" v-else-if='!has_topics'>
      <md-layout md-flex>
        <h4 md-flex class="mt-subheader mt-executing">
          <span class="mt-bold">Add torrent and press execute</span>
        </h4>
      </md-layout>
    </md-layout>
    <md-layout md-row md-gutter="24" class="mt-topics-header" v-else>
      <md-layout md-flex>
        <h4 md-flex class="mt-subheader mt-executing">
          <span class="mt-bold">Last Executed&nbsp;</span>at {{execute.finish_time | formatDate('HH:mm')}} ({{relative_execute}})
        </h4>
      </md-layout>
      <md-button class="md-icon-button" style="margin: auto 12px">
        <md-icon>input</md-icon>
      </md-button>
    </md-layout>
    <md-divider></md-divider>
  </div>
</template>

<script>
import moment from 'moment'

export default {
  props: ['loading', 'has_topics', 'execute'],
  computed: {
    'relative_execute': function () {
      return this.execute ? moment(this.execute.finish_time).fromNow() : '--'
    }
  },
  name: 'TopicsExecute'
}
</script>

<style scoped>
.mt-topics-header {
  padding: 0px 16px;
}

.mt-executing {
  text-overflow: ellipsis;
  overflow: hidden !important;
  white-space: nowrap;
}

.mt-bold {
  font-weight: 600;
}

.mt-subheader {
  font-size: 16px;
  font-weight: 400;
  letter-spacing: 0.010em;
  line-height: 24px;
}

.color-downloaded {
  background-color: #C8E6C9;
}

.color-failed {
  background-color: #FFCDD2;
}
</style>
