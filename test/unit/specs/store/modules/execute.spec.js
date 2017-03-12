import * as api from 'src/api/monitorrent'
import store from 'src/store/modules/execute'
import types from 'src/store/types'
import { expect } from 'chai'
import fetchMock from 'fetch-mock'
import Deferred from 'es2015-deferred'
import delay from 'delay'

describe('store/modules/execute', () => {
    const sandbox = sinon.sandbox.create()

    afterEach(() => {
        sandbox.restore()
        fetchMock.restore()
    })

    describe('mutations', () => {
        const stateBase = { loading: true, lastExecute: null, executing: false, currentExecuteLogs: [] }

        it('SET_LAST_EXECUTE', () => {
            let state = { ...stateBase }
            const execute = {finish_time: '2017-02-14T00:25:17+00:00'}

            expect(state.loading).to.be.true
            expect(state.lastExecute).to.be.null

            store.mutations[types.SET_LAST_EXECUTE](state, { execute })

            expect(state.loading).to.be.false
            expect(state.lastExecute).to.equal(execute)
        })

        it('LOAD_EXECUTE_FAILED', () => {
            const execute = {finish_time: '2017-02-14T00:25:17+00:00'}
            const state = { ...stateBase, lastExecute: execute }
            const err = new Error('Can not reach remote server')

            expect(state.lastExecute).to.equal(execute)
            expect(state.loading).to.be.true

            store.mutations[types.LOAD_EXECUTE_FAILED](state, { err })

            expect(state.lastExecute).to.equal(null)
            expect(state.loading).to.be.false
        })

        it('SET_EXECUTING', () => {
            const state = { ...stateBase }

            store.mutations[types.SET_EXECUTING](state, { value: true })

            expect(state).to.be.eql({ ...stateBase, ...{ executing: true } })
        })

        it('SET_CURRENT_EXECUTE_LOGS', () => {
            const state = { ...stateBase }
            const logs = [
                {execute_id: 12, id: 1200, level: 'info', message: 'Begin execute', time: '2017-02-11T19:09:29+00:00'}
            ]

            store.mutations[types.SET_CURRENT_EXECUTE_LOGS](state, { logs })

            expect(state).to.be.eql({ ...stateBase, ...{ currentExecuteLogs: logs } })
        })
    })

    describe('actions', () => {
        const logs = {
            count: 1,
            data: [
                {finish_time: '2017-02-14T01:35:47+00:00'}
            ]
        }

        it('loadLastExecute should works', async () => {
            sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(logs))

            const commit = sandbox.spy()

            await store.actions.loadLastExecute({ commit })

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_LAST_EXECUTE, { execute: logs.data[0] })
        })

        it('loadLastExecute should works with empty logs', async () => {
            const emptyLogs = {count: 0, data: []}
            sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(emptyLogs))

            const commit = sandbox.spy()

            await store.actions.loadLastExecute({ commit })

            expect(commit).to.have.been.calledOnce
            expect(commit).to.have.been.calledWith(types.SET_LAST_EXECUTE, { execute: null })
        })

        it('should throw on 3xx error response', async () => {
            var error = {topic: 'NotModified', description: 'Not Modified'}
            fetchMock.get(`/api/execute/logs?skip=0&take=1`, { status: 304, body: JSON.stringify(error) })

            const commit = sandbox.spy()

            await store.actions.loadLastExecute({ commit })

            expect(commit).have.been.calledOnce
            expect(commit.lastCall.args[0]).to.be.equal(types.LOAD_EXECUTE_FAILED)
        })

        it(`'watchExecute' should works`, async () => {
            const currentStub = sandbox.stub(api.default.execute, 'current')

            const deferred = new Deferred()

            currentStub.onCall(0).returns(Promise.resolve({is_running: false, logs: []}))
            currentStub.onCall(1).returns(Promise.resolve({is_running: true, logs: []}))
            currentStub.onCall(2).returns(Promise.resolve({is_running: true, logs: [{execute_id: 2345}]}))
            currentStub.onCall(3).returns(Promise.resolve({is_running: false, logs: []}))
            currentStub.onCall(4).returns(deferred.promise)

            const dispatchStub = sandbox.stub()

            const watchExecuteResult = store.actions.watchExecute({ dispatch: dispatchStub })

            expect(dispatchStub).to.have.been.calledOnce
            expect(dispatchStub).to.have.been.calledWith('executeCurrent')
            dispatchStub.reset()

            const executeCurrentPromise = store.actions.executeCurrent({ dispatch: dispatchStub })

            await delay(5)

            watchExecuteResult.unsubscribe()

            deferred.resolve({is_running: false, logs: []})

            const timeout = delay(5, 1)
            const resolved = await Promise.race([executeCurrentPromise.then(() => 2), timeout])

            expect(resolved).to.be.equal(2)

            expect(currentStub).to.have.been.callCount(5)
        })

        it(`'executeDetails' should works`, async () => {
            const executeId = 12
            const details = [
                {execute_id: 12, id: 1200, level: 'info', message: 'Begin execute', time: '2017-02-11T19:09:29+00:00'},
                {execute_id: 12, id: 1201, level: 'info', message: 'Begin execute tracker.com', time: '2017-02-11T19:09:31+00:00'},
                {execute_id: 12, id: 1202, level: 'downloaded', message: 'Downlaoded something', time: '2017-02-11T19:09:33+00:00'},
                {execute_id: 12, id: 1203, level: 'info', message: 'End execute tracker', time: '2017-02-11T19:09:35+00:00'},
                {execute_id: 12, id: 1204, level: 'info', message: 'End execute', time: '2017-02-11T19:09:37+00:00'}
            ]
            const state = { loading: true, lastExecute: null, executing: false, currentExecuteLogs: [] }

            sandbox.stub(api.default.execute, 'logs', () => Promise.resolve(logs))

            const detailsStub = sandbox.stub(api.default.execute, 'details')

            detailsStub.withArgs(12, null).onFirstCall().returns(Promise.resolve({is_running: true, logs: []}))
            detailsStub.withArgs(12, null).onSecondCall().returns(Promise.resolve({is_running: true, logs: details.slice(0, 1)}))
            detailsStub.withArgs(12, 1200).returns(Promise.resolve({is_running: true, logs: details.slice(1, 3)}))
            detailsStub.withArgs(12, 1202).returns(Promise.resolve({is_running: true, logs: details.slice(3, 4)}))
            detailsStub.withArgs(12, 1203).returns(Promise.resolve({is_running: false, logs: details.slice(4)}))
            detailsStub.throws()

            const commit = sandbox.spy()

            await store.actions.executeDetails({ commit, state }, { id: executeId })

            expect(commit).to.have.been.calledWith(types.SET_EXECUTING, { value: true })
            expect(commit).to.have.been.calledWith(types.SET_CURRENT_EXECUTE_LOGS, { logs: [] })
            expect(commit).to.have.been.calledWith(types.SET_CURRENT_EXECUTE_LOGS, { logs: details.slice(0, 1) })
            expect(commit).to.have.been.calledWith(types.SET_CURRENT_EXECUTE_LOGS, { logs: details.slice(0, 3) })
            expect(commit).to.have.been.calledWith(types.SET_CURRENT_EXECUTE_LOGS, { logs: details.slice(0, 4) })
            expect(commit).to.have.been.calledWith(types.SET_CURRENT_EXECUTE_LOGS, { logs: details })
            expect(commit).to.have.been.calledWith(types.SET_LAST_EXECUTE, { execute: logs.data[0] })
            expect(commit).to.have.been.calledWith(types.SET_EXECUTING, { value: false })
        })

        it(`'executeDetails' with unexpected logs`, async () => {
            const executeId = 12
            const details = [
                {execute_id: 12, id: 1200, level: 'info', message: 'Begin execute', time: '2017-02-11T19:09:29+00:00'},
                {execute_id: 12, id: 1201, level: 'info', message: 'Begin execute tracker.com', time: '2017-02-11T19:09:31+00:00'},
                {execute_id: 12, id: 1202, level: 'downloaded', message: 'Downlaoded something', time: '2017-02-11T19:09:33+00:00'},
                {execute_id: 12, id: 1203, level: 'info', message: 'End execute tracker', time: '2017-02-11T19:09:35+00:00'},
                {execute_id: 12, id: 1204, level: 'info', message: 'End execute', time: '2017-02-11T19:09:37+00:00'}
            ]
            const state = { loading: true, lastExecute: null, executing: false, currentExecuteLogs: [] }

            sandbox.stub(api.default.execute, 'logs', () => Promise.resolve({ ...logs, ...{ data: [] } }))

            sandbox.stub(api.default.execute, 'details', () => Promise.resolve({is_running: false, logs: details}))

            const commit = sandbox.spy()

            await store.actions.executeDetails({ commit, state }, { id: executeId })

            expect(commit).to.have.been.calledWith(types.SET_EXECUTING, { value: true })
            expect(commit).to.have.been.calledWith(types.SET_CURRENT_EXECUTE_LOGS, { logs: details })
            expect(commit).to.have.been.calledWith(types.SET_LAST_EXECUTE, { execute: null })
            expect(commit).to.have.been.calledWith(types.SET_EXECUTING, { value: false })
        })
    })
})
