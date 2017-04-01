import { play } from 'vue-play'
import TopicsExecute from '../../../src/components/Topics/TopicsExecute'
import moment from 'moment'

const execute = {finish_time: moment().subtract(43, 'minutes'), failed: 0, downloaded: 0}
const trackers = ['lostfilm.tv', 'rutor.org']
const executingLogs = [
    {level: 'info', message: 'Message 1'},
    {level: 'info', message: 'Message 2'},
    {level: 'info', message: 'Message 3'}
]
const failedLog = {level: 'failed', message: 'Failed'}
const downloadedLog = {level: 'downloaded', message: 'Failed'}

play(TopicsExecute)
    .add('loading', h => <TopicsExecute loading={true}></TopicsExecute>)
    .add('never execute', h => <TopicsExecute></TopicsExecute>)
    .add('never execute with trackers', function (h) {
        const onExecuteTracker = tracker => this.$log(`Execute: ${tracker}`)
        const onExecute = () => this.$log(`Execute: All`)
        return <TopicsExecute trackers={trackers} onExecute={onExecute} onExecute-tracker={onExecuteTracker}></TopicsExecute>
    })
    .add('executed 43 minutes ago', h => <TopicsExecute execute={execute}></TopicsExecute>)
    .add('executed 43 minutes ago with failed', h => <TopicsExecute execute={{...execute, failed: 1}}></TopicsExecute>)
    .add('executed 43 minutes ago with downloaded', h => <TopicsExecute execute={{...execute, failed: 0, downloaded: 1}}></TopicsExecute>)
    .add('executed 43 minutes ago with failed and downloaded', h => <TopicsExecute execute={{...execute, failed: 1, downloaded: 1}}></TopicsExecute>)
    .add('executing', h => <TopicsExecute executing={true}></TopicsExecute>)
    .add('executing with one log', h => <TopicsExecute executing={true} executingLogs={[executingLogs[0]]}></TopicsExecute>)
    .add('executing with logs', h => <TopicsExecute executing={true} executingLogs={executingLogs}></TopicsExecute>)
    .add('executing with logs should reset last execute status color', h => <TopicsExecute execute={{...execute, failed: 1}} executing={true} executingLogs={executingLogs}></TopicsExecute>)
    .add('executing with logs failed color', h => <TopicsExecute execute={{...execute, failed: 1}} executing={true} executingLogs={[failedLog, ...executingLogs]}></TopicsExecute>)
    .add('executing with logs downloaded color', h => <TopicsExecute execute={{...execute, failed: 1}} executing={true} executingLogs={[downloadedLog, ...executingLogs]}></TopicsExecute>)
