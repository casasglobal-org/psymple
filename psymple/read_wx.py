# -*- coding: utf-8 -*-
"""
Created on Tue Feb  2 23:00:56 2021

@author: Jose Ricardo Cure
"""
class Weather(object):
    def __init__(self):
        super().__init__()

    def filterWX(wx,startM,startD,startY,endM,endD,endY,weatherfile):
        '''locate dates to run in weather file and call main'''
        start=False
        end=False
        cont=3

        keyStart= str(startM) +' '+ str(startD)+' ' + str(startY)
        keyEnd= str(endM)+' ' + str(endD)+' ' + str(endY)
        print(keyStart, keyEnd)
        for sList in (wx):
            if cont < len(wx):
                #cont  = cont+1
                keyWX = str(wx[cont][0])+' ' +  str(wx[cont][1])+' ' + str(wx[cont][2])
                if keyWX == keyStart:
                    if start==False:
                        index_start = cont
                        start=True
                        lat   = float(wx[1][0])
                        long  = float(wx[1][1])
                        month = int(wx[cont][0])
                        day   = int(wx[cont][1])
                        year  = int(wx[cont][2])
                        tmax  = float(wx[cont][3])
                        tmin  = float(wx[cont][4])
                        solar = float(wx[cont][5])
                        precip= float(wx[cont][6])
                        rh    = float(wx[cont][7])
                        wind  = float(wx[cont][8])
                        #print('   first date to run '+ str(month) +' ' + str(day) + ' ' + str(year))
                        weatherfile.append([lat,long,month,day,year, tmax,tmin,solar,precip,rh,wind])

                elif keyWX == keyEnd:
                    if end == False:
                        index_finish = cont+1
                        totdays = index_finish - cont
                        keyWX = str(wx[cont][0])+' ' +  str(wx[cont][1])+' ' + str(wx[cont][2])
                        end=True
                        #print('   last date to run '+ str(month) +' ' + str(day) + ' ' + str(year)+ '  ')
                        #print( '.. total simulation days in this file = '+str(totdays) )

                cont=cont+1
                if end==False and start == True:
                    lat   = float(wx[1][0])
                    long  = float(wx[1][1])
                    month = int(wx[cont][0])
                    day   = int(wx[cont][1])
                    year  = int(wx[cont][2])
                    tmax  = float(wx[cont][3])
                    tmin  = float(wx[cont][4])
                    solar = float(wx[cont][5])
                    precip= float(wx[cont][6])
                    rh    = float(wx[cont][7])
                    wind  = float(wx[cont][8])
                    weatherfile.append([lat,long,month,day,year, tmax,tmin,solar,precip,rh,wind])



    def readwx(wx_dir,startM,startD,startY,endM,endD,endY,weatherfile):
        '''read weather file'''
        with open (wx_dir , 'r') as f: # use with to open your files, it close them automatically
            wx = [x.split() for x in f]
            wxfile= wx[0] # title of the wx file
            lat   = float(wx[1][0])
            long  = float(wx[1][1])
            print()
            print('weather file ', wxfile)
            print(' latitude '+ str(lat), ' longitude '+ str(long))
            print('.. original number of days in WX file = ' + str(len(wx)))
            Weather.filterWX(wx,startM,startD,startY,endM,endD,endY,weatherfile)
            return weatherfile



#in_locations = 'd:/fruit_flies/r_USA_MEX_observed_1980-2010_AgMERRA_coarse_test.txt'
#weatherfile = Weather.run_locations(in_locations)



