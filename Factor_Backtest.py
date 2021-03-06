import datetime
from technical_factor import Technical_Factor
import backtrader as bt
import backtrader.feeds as btfeed
import pandas as pd

def get_data(start_date, end_date):
    data = pd.read_csv('./data/000001.SH.csv', parse_dates=[0], index_col=0)
    data.dropna(inplace=True)
    data.index = pd.to_datetime(data.index)
    data['ts_code'] = '000001.SH'
    data.rename(columns={'CLOSE': 'PX_LAST', 'OPEN': 'PX_OPEN', 'HIGH': 'PX_HIGH', 'LOW': 'PX_LOW',
                         'VOLUME': 'PX_VOLUME'}, inplace=True)
    data = data[start_date: end_date]
    return data

class GenericCSV_Signal(btfeed.GenericCSVData):
    lines = ('signal',)
    params = (('signal', 6),)

class Technical_Strategy(bt.Indicator):
    lines = ('signal',)
    params = (('signal', 6),)

    def __init__(self):
        self.lines.signal = self.datas[0].signal




if __name__ == '__main__':

    start_date = '2021-01-01'
    end_date = '2022-01-01'
    data = get_data(start_date, end_date)
    temp = data.copy()
    factor_list = ['ROC', 'MA', 'SMA', 'DMA', 'MACD', 'TRIX', 'BBI', 'BOLL', 'Aberration', 'BIAS', 'CCI', 'KDJ', 'RSI', 'CMO', 'RHL', 'KING']

    res_list = []
    for factor in factor_list:
        t1 = Technical_Factor()
        df = eval('t1.%s_(temp)' % factor)
        df = df.loc[:, ['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST', 'PX_VOLUME', factor+'_']]
        filename = factor+'.csv'
        df.to_csv(filename)

        cb = bt.Cerebro()

        data = GenericCSV_Signal(
            dataname = filename,

            fromdate = datetime.datetime(int(start_date.split('-')[0]), int(start_date.split('-')[1]), int(start_date.split('-')[2])),
            todate = datetime.datetime(int(end_date.split('-')[0]), int(end_date.split('-')[1]), int(end_date.split('-')[2])),

            dtformat = ('%Y-%m-%d'),

            datetime = 0,
            open = 1,
            high = 2,
            low = 3,
            close = 4,
            volume = 5,
            signal = 6,
            openinterest = -1
        )

        cb.adddata(data)
        cb.add_signal(bt.SIGNAL_LONG, Technical_Strategy, subplot=True)
        cb.broker.setcash(5000.0)
        cb.addsizer(bt.sizers.FixedSize, stake=1)
        cb.broker.setcommission(commission=0)
        a = bt.analyzers.SharpeRatio_A
        a.riskfreerate = 0.0
        cb.addanalyzer(a, _name='sharpe')
        cb.addanalyzer(bt.analyzers.Returns, _name='ret')
        cb.addanalyzer(bt.analyzers.Calmar, _name='calmar')
        cb.addanalyzer(bt.analyzers.DrawDown, _name='drawdone')
        cb.addanalyzer(bt.analyzers.TradeAnalyzer, _name='analyzer')
        cb.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')

        run = cb.run()
        a = run[0].analyzers.analyzer.get_analysis()
        try:
            res = [run[0].analyzers.analyzer.get_analysis()['pnl']['gross']['total'],
                   run[0].analyzers.analyzer.get_analysis()['won']['pnl']['average'],
                   run[0].analyzers.analyzer.get_analysis()['lost']['pnl']['average'],
                   # run[0].analyzers.ret.get_analysis()['rnorm'],
                    run[0].analyzers.sharpe.get_analysis()['sharperatio'],
                    run[0].analyzers.drawdone.get_analysis()['max']['drawdown']/100,
                    run[0].analyzers.analyzer.get_analysis()['won']['total'] /
                    run[0].analyzers.analyzer.get_analysis()['long']['total'],
                    run[0].analyzers.analyzer.get_analysis()['long']['total'],
                    ]
            res_list.append(res)
            print(factor+' done')
        except:
            res_list.append([None]*7)
            print(factor, ' No trade finished')

        cb.plot()

    res_df = pd.DataFrame(res_list,
                          columns=['total pnl', 'avg won pnl', 'avg lost pnl', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'trade_times'],
                          index=factor_list)
    res_df.to_csv('./result/result_1.csv')
    print('done')
