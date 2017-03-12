<template>
    <div ref="root" :class="{ 'color-failed': execute && execute.failed > 0, 'color-downloaded': execute && execute.failed == 0 && execute.downloaded > 0 }">
        <md-layout md-row md-gutter="24" class="mt-topics-header" v-if='loading'>
            <md-layout md-flex>
                <h4 ref="loading" md-flex class="mt-subheader mt-executing">
                    <span class="mt-bold">Updating torrents...</span>
                </h4>
            </md-layout>
        </md-layout>
        <md-layout md-row md-gutter="24" class="mt-topics-header" v-else>
            <md-layout md-flex>
                <h4 ref="lastExecute" md-flex class="mt-subheader mt-executing">
                    <span class="mt-bold">Last Executed:&nbsp;</span>
                    <span v-if="execute">at {{execute.finish_time | formatDate('HH:mm')}} ({{relativeExecute}})</span>
                    <span v-else>never</span>
                </h4>
            </md-layout>
            <md-menu ref="executeMenu" class="md-list-action" md-direction="bottom left" md-size="5" style="margin: auto 12px">
                <md-button class="md-icon-button" md-menu-trigger>
                    <md-icon>input</md-icon>
                </md-button>
                <md-menu-content md-size="4">
                    <md-menu-item>
                        <md-icon>input</md-icon><span>Execute All</span>
                    </md-menu-item>
                    <md-menu-item ref="executeMenuItem" v-for="tracker of trackers">
                        <md-icon>input</md-icon><span>Execute <b>{{tracker}}</b></span>
                    </md-menu-item>
                </md-menu-content>
            </md-menu>
        </md-layout>
        <md-progress ref="progress" md-indeterminate :style="{opacity: executing ? 1 : 0}"></md-progress>
        <md-divider></md-divider>
    </div>
</template>

<script>
import moment from 'moment'

export default {
    props: {
        loading: {
            type: Boolean
        },
        execute: {
            type: Object
        },
        executing: {
            type: Boolean,
            default: false
        },
        trackers: {
            type: Array
        }
    },
    computed: {
        'relativeExecute': function () {
            return moment(this.execute.finish_time).fromNow()
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
