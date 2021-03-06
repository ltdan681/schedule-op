# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 17:13:02 2020

@author: ltdan
"""

from ortools.sat.python import cp_model
import numpy as np
import matplotlib.pyplot as plt


def main():
    
    np.random.seed(936)
    
    #define the variables
    residents = 4
    weeks = 4
    shifts = weeks * 21
    
    total_residents = range(residents)
    total_shifts = range(shifts)
    shift_requests = np.random.randint(2, size = (residents, shifts)) 

    min_per_shift = 1
    max_per_shift = 2

    num_shifts_req = 0
    
    for r in total_residents:
        for s in total_shifts:
            num_shifts_req += shift_requests[r][s]


    
    #create the model
    shift_model = cp_model.CpModel()


    x = {}
    for r in total_residents:
        for s in total_shifts:
            x[(r,s)] = shift_model.NewBoolVar('x_r%is%i' % (r,s))
            
    y = {}
    for r in total_residents:
        for s in total_shifts:
            y[(r,s)] = shift_model.NewBoolVar('y_r%is%i' % (r,s))
     
    #Bool for if a resident works on a specific day
    z = {}
    for r in total_residents:
        for w in range(0, shifts, 21):
            for d in range(w, w+21, 3):
                z[(r,w,d)] = shift_model.NewBoolVar('z_r%iw%id%i' % (r,w,d))
            
    
    
    #Contraints
    
    #Every shift must have at least min_per_shift residents and less than max_per_shift
    for s in total_shifts:
       shift_model.Add(sum(x[r,s] for r in total_residents) >= min_per_shift)
       shift_model.Add(sum(x[r,s] for r in total_residents) <= max_per_shift)
       
       
    #Max number of shifts restraint 
    
    for r in total_residents:
        shift_model.Add(sum(x[r,s] for s in total_shifts) <= 40)
        shift_model.Add(sum(x[r,s] for s in total_shifts) >= 30)
      
   
    #3+2 constraint
    
    for r in total_residents:
        for s in range(shifts - 4):
            pattern_1 = x[(r,s)] + x[(r, s+1)] + x[(r, s+2)]
            shift_model.Add(3 > pattern_1 + y[(r,s)] * 100)
            shift_model.Add(3 <= pattern_1 + (1 - y[(r,s)]) * 100)
            shift_model.Add(y[(r,s)] + x[(r, s+3)] <= 1)
            shift_model.Add(y[(r,s)] + x[(r, s+4)] <= 1)
        
        edge = x[(r, shifts-1)] + x[(r, shifts-2)]+ x[(r, shifts-3)] + x[(r, shifts-4)] 
        shift_model.Add(edge < 4)

        
    #weekly constraint
    
    for r in total_residents:
        for w in range(0, shifts, 21):
            weekly_total = 0
            for d in range(w, w+21, 3):
                daily_total = x[(r, d)] + x[(r, d+1)] + x[(r,d+2)]
                
                #Turns z on if r works day d
                shift_model.Add(daily_total >= 1 - (1 - z[(r,w,d)]) * 100)   
                shift_model.Add(daily_total < 1 + z[(r,w,d)] * 100)
                weekly_total += z[(r,w,d)]
            #can work max 6 days a week
            shift_model.Add(weekly_total <= 6)

    #Opjective
    shift_model.Maximize(
        sum(shift_requests[r][s] * x[(r,s)] for r in total_residents
            for s in total_shifts))
    
    #Solver
    solver = cp_model.CpSolver()
    solver.Solve(shift_model)
    

    
    #Stats
    print()
    print('Statistics')
    print('Number of requests met = %i' % solver.ObjectiveValue(),
          '(out of %i)' % num_shifts_req)
    print("Walltime: %f s" % solver.WallTime())
    
    for r in total_residents:
        num_shifts = 0
        for s in total_shifts:
            num_shifts += solver.Value(x[(r,s)])
        print('Res ', r, ' has ', num_shifts, 'shifts')
        
    #Grid plot of schedule
    
    shift_matrix = []
    value_matrix = []
    for r in total_residents:
        shift_result = []
        value = 0
        tot_shifts = 0
        for s in total_shifts:
            if solver.Value(x[(r,s)]) == 1:
                value = value + shift_requests[r][s]
                tot_shifts = tot_shifts + 1
                if shift_requests[r][s] == 1:
                    shift_result.append((128,128,128))
                else:
                    shift_result.append((204,51,0))
            else:
                shift_result.append((224,224,224))
        shift_matrix.append(shift_result)
        value_matrix.append((r,tot_shifts,value))
        
    plt.figure(figsize = (8,3))
    
    plt.imshow(shift_matrix, aspect = 3)
    plt.axvline(20.5, color = 'black')
    plt.axvline(41.5, color = 'black')
    plt.axvline(62.5, color = 'black')
    
    #add borders
    
    for r in total_residents:
        for s in total_shifts:
            rec = plt.Rectangle((s-0.5,r-0.5), 1, 1, 
                                facecolor = 'none', 
                                edgecolor = 'white', 
                                linewidth=1)
            plt.gca().add_patch(rec)
                    
    week_set = [10.5,31.5,52.5,73.5]
    plt.tick_params(axis='both', bottom=False)
    plt.xticks(week_set,['Week 1', 'Week 2','Week 3','Week 4'],fontsize=10)
    plt.yticks([0,1,2,3],['R1','R2','R3','R4'],fontsize=8)
    plt.tick_params(axis = "both", which = "both", bottom = False, left = False)
    

if __name__ == '__main__':
    main()

