etf-analysis
============

### Does the market capitalization of an electronically traded fund match its underlying asset value? ###

No.

On Jan 11, I ran the analysis on iShares Core S&P 500 ETF (IVV) with the following results:

 ```
Name:	iShares Core S&P 500 ETF
Symbol:	IVV
Id:	239726
CSV URL:	https://www.ishares.com/us/products/239726/ishares-phlx-semiconductor-etf/1467271812596.ajax?fileType=csv&fileName=SOXX_holdings&dataType=fund


              open    high     low   close   volume
date                                               
2019-01-11  259.24  260.52  258.57  260.37  5111675


Estimated holdings value of IVV:	162,938,811,602.75012
Estimated market capitalization of IVV:	155,258,631,000.0
Undercapitalization:	155,258,631,000.0
Ratio:	0.049467

```

The underlying holdings are worth $155,258,631,000.00 more that the market capitalization. This is ~5% of the market capitalization.

What's going on?

Checkout my other projects at https://jakebillings.com.