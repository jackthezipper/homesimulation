import math
import csv
import random

import Common
import Timer
import Agent
import Activity
import Global

BIOPROPERTY = {
"Hunger" : Common.BIOLOGICAL_PROPERTY_HUNGER,
"Dirty" : Common.BIOLOGICAL_PROPERTY_DIRTY,
"Thirst" : Common.BIOLOGICAL_PROPERTY_THIRSTY,
"Defecate" : Common.BIOLOGICAL_PROPERTY_DEFECATE,
"Urinate" : Common.BIOLOGICAL_PROPERTY_URINATE,
"Energy" : Common.BIOLOGICAL_PROPERTY_ENERGY,
"Exhausted" : Common.BIOLOGICAL_PROPERTY_TIRED,
"Sleepy" : Common.BIOLOGICAL_PROPERTY_SLEEPY,
}

K_MET_AWAKE = 0.033
K_MET_ASLEEP = 0.015

def Fmt(val):
	return "{:.3f}".format(float(val))

class BioProperty():
	def __init__(self, agent, type, rate, current):
		self.m_agent = agent
		self.m_type = type
		self.m_rate = rate
		self.m_relatedActivity = None
		self.m_relatedActivityId = ""
		self.m_currentScore = current
	
	def TryTriggerRelatedActivity(self):
		activityToTrigger = ""
		activity = self.m_agent.GetActivityById(self.m_relatedActivityId)
		
		# if len(activity.m_prequisite) > 0:
			# activity = self.m_agent.GetActivityById(activity.m_prequisite[0])
		
		if activity != None and activity.CanStart(self.m_agent):
			activityToTrigger = self.m_relatedActivityId
		
		Global.Logger.LogDebug("try trigger "+self.m_relatedActivityId+"|"+activityToTrigger+"\n")
		
		if activityToTrigger != "":
			self.m_relatedActivity = self.m_agent.TryTrigger(activityToTrigger)
	
	def PrintProperty(self):
		pass
	
	def GetCalcParam(self):
		return []
	
	def ProcessOutput(self):
		output = [Global.g_timer.GetFormattedHour()]
		output.extend(self.GetCalcParam())
		return output

class Hunger(BioProperty):
	def __init__(self, agent, type, rate, current, habit, threshold):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_habit = habit
		self.m_totalScore = current
		self.m_threshold = threshold
		self.m_constraintEffectScore = 0
		self.m_lastEatHour = -1
		self.m_pointEffect = 0
		self.m_mlUrinate = 0
		self.m_pointHunger = 0
		self.m_currentRate = 0
		self.m_activityEffect = 0;
		# self.m_constraint = 0
		self.m_relatedActivityId = "A119"
		self.m_eatActivity = self.m_agent.GetActivityById("B02")
		self.m_energyStorage = current#self.m_threshold[Common.HUNGER_LIMIT_DOWN] * 0.05  / 60#self.m_agent.GetActivityById(self.m_relatedActivityId).m_duration
		self.K_COLUMN_NAME = ["Hari", "MAKAN", "Energy Storage","Tingkat Kalori yang Dibutuhkan Saat Ini", "Laju Lapar", "Efek Aktivitas", "Pengaruh Emosi", "Total Lapar 1 jam berikutnya", "Kebiasaan", "Constraint Efek Makan", "Konversi Kalori ke Poin", "Konversi Poin ke mL(URINASI)"]
	
	def CalculateScore(self):
		deltaHour = (Global.g_timer.GetHour() - self.m_lastEatHour) % 24
		if self.m_agent.IsAsleep():
			self.m_currentRate = self.m_rate[Common.AGENT_ASLEEP]
		elif self.IsHabit(Global.g_timer.GetHour()):
			if deltaHour < 3 :
				self.m_currentRate = self.m_rate[Common.AGENT_CUST_COND]
			else:
				self.m_currentRate = self.m_rate[Common.AGENT_CUST_COND2]
		else:
			self.m_currentRate = self.m_rate[Common.AGENT_AWAKE]
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		# self.m_energyStorage = (self.m_constraintEffectScore * 0.05 * self.m_eatActivity.m_duration / 60) if (self.m_constraintEffectScore > 0) else self.m_energyStorage
		self.m_energyStorage = self.m_totalScore + self.m_constraintEffectScore
		# self.m_currentRate = self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else (Common.AGENT_AWAKE if (self.m_lastEatHour == -1 or deltaHour>3) else Common.AGENT_CUST_COND)]
		
	
	def PostUpdateActivityCalculation(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			self.m_constraintEffectScore = 0
			self.m_pointEffect = 0
			self.m_mlUrinate = 0
			return
		self.m_activityEffect = self.m_agent.m_weight * self.m_agent.GetActivityEffect(self.m_type)
		self.m_currentScore = -self.m_activityEffect + self.m_agent.GetEmotionalFactor() + self.m_currentRate
		self.m_totalScore = max(0,self.m_energyStorage - self.m_currentScore)
		self.CalculateEffect()
		self.m_pointHunger = Common.clamp(10 * (self.m_totalScore - self.m_threshold[Common.HUNGER_LIMIT_DOWN]) / (self.m_rate[Common.RATE_BASE] - self.m_threshold[Common.HUNGER_LIMIT_DOWN]),0,10)
		self.m_pointEffect = self.m_constraintEffectScore / self.m_rate[Common.RATE_BASE] * 10
		self.m_mlUrinate = self.m_constraintEffectScore * 0.12959782
	
	def CalculateEffect(self):
		if self.IsHabit(Global.g_timer.GetHour()):
			Global.Logger.LogDebug("hunger "+self.m_agent.m_role+" "+str(self.m_eatActivity.IsRunning())+" "+str(self.m_eatActivity.m_status)+" "+str(self.m_relatedActivity)+"\n")
			Global.Logger.LogDebug("turigs "+str(self.m_lastEatHour)+" "+str(self.m_totalScore)+" "+str(self.m_threshold[Common.HUNGER_LIMIT_UP])+"\n")
			cond = (((self.m_lastEatHour == -1) or (((Global.g_timer.GetHour() - self.m_lastEatHour) % 24) > 2)) and self.m_totalScore < self.m_threshold[Common.HUNGER_LIMIT_UP] and self.m_relatedActivity == None and not self.m_eatActivity.IsRunning() and not self.m_eatActivity.m_status == Common.ACT_STATUS_GOTO)
			Global.Logger.LogDebug("cond "+str(cond)+"\n")
			if ((self.m_lastEatHour == -1) or (((Global.g_timer.GetHour() - self.m_lastEatHour) % 24) > 2)) and self.m_totalScore < self.m_threshold[Common.HUNGER_LIMIT_UP] and self.m_relatedActivity == None and not self.m_eatActivity.IsRunning() and not self.m_eatActivity.m_status == Common.ACT_STATUS_GOTO:
				self.TryTriggerRelatedActivity()
		
		if self.m_eatActivity.IsRunning():
			if self.m_constraintEffectScore == 0:
				self.m_constraintEffectScore = (self.m_rate[Common.RATE_BASE] - self.m_totalScore) / self.m_eatActivity.m_duration
				self.m_lastEatHour = Global.g_timer.GetHour()
		else:
			self.m_constraintEffectScore = 0
	
	def GetScore(self):
		convertPoint = Common.clamp(10 * (self.m_energyStorage - self.m_threshold[Common.HUNGER_LIMIT_DOWN]) / (self.m_rate[Common.RATE_BASE] - self.m_threshold[Common.HUNGER_LIMIT_DOWN]),0,10)
		return convertPoint
	
	def IsHabit(self, time):
		if self.m_habit == None:
			return False
		return self.m_habit[time]
	
	def TryTriggerRelatedActivity(self):
		if self.m_relatedActivity == None and not (self.m_eatActivity.IsRunning() or self.m_eatActivity.m_status == Common.ACT_STATUS_GOTO):
			BioProperty.TryTriggerRelatedActivity(self)
		else:
			Global.Logger.LogDebug("cancel trigger\n")
	
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_currentRate)+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_totalScore)+" "+("K" if self.IsHabit(Global.g_timer.GetHour()) else "-")+" "+Fmt(self.m_currentEffectScore)+" "+Fmt(self.m_mlUrinate)+" "+Fmt(self.m_pointHunger)+"\n")
	
	def GetCalcParam(self):
		return [Fmt(self.m_energyStorage), Fmt(self.m_currentScore), Fmt(self.m_currentRate), Fmt(self.m_agent.GetActivityEffect(self.m_type)), Fmt(self.m_agent.GetEmotionalFactor()), Fmt(self.m_totalScore), ("K" if self.IsHabit(Timer.GetInstance().GetHour()) else "-"), Fmt(self.m_constraintEffectScore), Fmt(self.m_pointHunger), Fmt(self.m_mlUrinate)]
	
	def ProcessOutput(self):
		output = [Global.g_timer.GetDay(), Global.g_timer.GetFormattedHour()]
		output.extend(self.GetCalcParam())
		return output

class Thirst(BioProperty):
	def __init__(self, agent, type, rate, current, habit, effect):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_habit = habit
		self.m_effect = effect
		self.m_totalScore = current
		self.m_currentEffectScore = 0
		self.m_mlUrinate = 0
		self.m_relatedActivityId = "B03"
		self.K_COLUMN_NAME = ["MINUM", "Tingkat Haus Terkini", "Laju Haus", "Efek Aktivitas", "Pengaruh Emosi", "Total Haus 1 jam berikutnya", "Kebiasaan", "Efek Minum", "Konversi poin ke mL (URINASI)"]
		
	def CalculateScore(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		self.m_currentScore = self.m_totalScore - self.m_currentEffectScore + self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
	
	def CalculateEffect(self):
		if self.m_agent.GetProperty("Hunger").m_eatActivity != None and self.m_agent.GetProperty("Hunger").m_eatActivity.IsRunning():
			return (self.m_effect[Common.EFFECT_HABIT_NONHABIT][Common.EFFECT_NEW_VALUE] if self.m_totalScore > self.m_effect[Common.EFFECT_EAT][Common.EFFECT_NEW_LIMIT] else self.m_effect[Common.EFFECT_EAT][Common.EFFECT_NEW_VALUE]) / self.m_agent.GetProperty("Hunger").m_eatActivity.m_duration
		
		index = Common.EFFECT_HABIT_HABIT if self.IsHabit(Global.g_timer.GetHour()) else Common.EFFECT_HABIT_NONHABIT
		#print("rolade "+str(self.m_relatedActivity)+" "+Fmt(self.m_totalScore)+" "+Fmt(self.m_effect[index][Common.EFFECT_NEW_LIMIT]))
		if self.m_relatedActivity == None and self.m_totalScore >= self.m_effect[index][Common.EFFECT_NEW_LIMIT]:
			#print("TARIGAX")
			self.TryTriggerRelatedActivity()
		
		if (self.m_relatedActivity != None and self.m_relatedActivity.IsRunning()):
			return self.m_effect[index][Common.EFFECT_NEW_VALUE] / self.m_relatedActivity.m_duration
		
		return 0
	
	def PostUpdateActivityCalculation(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			self.m_mlUrinate = 0
			self.m_currentEffectScore = 0
			return
		self.m_totalScore = Common.clamp((self.m_currentScore + (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type)),0,10)
		self.m_mlUrinate = 15 * self.m_currentEffectScore
		self.m_currentEffectScore = self.CalculateEffect()
		self.PrintProperty()
	
	def IsHabit(self, time):
		if self.m_habit == None:
			return False
		return self.m_habit[time]
	
	def GetScore(self):
		return self.m_totalScore
		
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_totalScore)+" "+("K" if self.IsHabit(Global.g_timer.GetHour()) else "-")+" "+Fmt(self.m_currentEffectScore)+" "+Fmt(self.m_mlUrinate)+"\n")
	
	def GetCalcParam(self):
		return [Fmt(self.m_currentScore), Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]), Fmt(self.m_agent.GetActivityEffect(self.m_type)), Fmt(self.m_agent.GetEmotionalFactor()), Fmt(self.m_totalScore), ("K" if self.IsHabit(Timer.GetInstance().GetHour()) else "-"), Fmt(self.m_currentEffectScore), Fmt(self.m_mlUrinate)]
	
	# def ProcessOutput(self):
		# # pass
		# return [Global.g_timer.GetFormattedHour(), 
	
class Dirty(BioProperty):
	def __init__(self, agent, type, rate, current, habit, effect ):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_habit = habit
		self.m_effect = effect
		self.m_totalScore = current
		self.m_constraint = current
		self.m_currentEffectScore = 0
		self.m_relatedActivityId = "B07"
		self.m_lastBathHour = -1
		self.K_COLUMN_NAME = ["KOTOR","Tingkat Kotor Terkini", "Laju Kotor", "Efek Aktivitas", "Pengaruh Emosi","Total kotor 1 jam berikutnya", "Kebiasaan Mandi","Efek Mandi", "Constraint"]
	
	def CalculateScore(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		self.m_currentScore = self.m_constraint
		self.m_totalScore = max(0,(self.m_currentScore + (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type) ))
		
	def CalculateEffect(self):
		if self.m_relatedActivity == None and self.m_totalScore > self.m_effect and self.IsHabit(Global.g_timer.GetHour()):
			self.TryTriggerRelatedActivity()
		if (self.m_relatedActivity != None and self.m_relatedActivity.IsRunning()):
			if self.m_currentEffectScore == 0:
				self.m_currentEffectScore = -self.m_totalScore / self.m_relatedActivity.m_duration
				self.m_lastBathHour = Global.g_timer.GetHour()
		else:
			self.m_currentEffectScore = 0
	
	def PostUpdateActivityCalculation(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			self.m_currentEffectScore = 0
			return
		self.CalculateEffect()
		
		self.m_constraint = self.m_totalScore + self.m_currentEffectScore
		if self.IsHabit(Global.g_timer.GetHour()) and ((Global.g_timer.GetHour() - self.m_lastBathHour) % 24 > 2) and self.m_totalScore < self.m_effect and (self.m_relatedActivity == None or not self.m_relatedActivity.IsRunning()):
			self.m_constraint += ((random.random() * 3) + 2)/Timer.MINUTE_IN_HOUR #bottom value 2, range 3, max value 5
		# self.m_totalScore += self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] + self.m_currentEffectScore
		# self.m_totalScore = Common.clamp(self.m_totalScore, 0, 10)
	
	def IsHabit(self, time):
		if self.m_habit == None:
			return False
		return self.m_habit[time]
	
	def GetScore(self):
		return self.m_constraint
	
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_totalScore)+" "+("M" if self.IsHabit(Global.g_timer.GetHour()) else "-")+" "+Fmt(self.m_currentEffectScore)+"\n")
	
	def GetCalcParam(self):
		return [Fmt(self.m_currentScore), Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]), Fmt(self.m_agent.GetActivityEffect(self.m_type)), Fmt(self.m_agent.GetEmotionalFactor()), Fmt(self.m_totalScore), ("M" if self.IsHabit(Timer.GetInstance().GetHour()) else "-"), Fmt(self.m_currentEffectScore), Fmt(self.m_constraint)]
		
	# def ProcessOutput(self):
	# #self.K_COLUMN_NAME = ["KOTOR",					"Tingkat Kotor Terkini", "Laju Kotor", 																				"Efek Aktivitas", 								"Pengaruh Emosi",						"Total kotor 1 jam berikutnya", "Kebiasaan Mandi",										"Efek Mandi", 					"Constraint"]
		# return [Global.g_timer.GetFormattedHour(), 

class Energy(BioProperty):
	def __init__(self, agent, type, rate, current):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_scoreActAndEmo = 0
		self.m_eatEffect = 0
		self.m_totalScore = current
		self.m_pointEnergy = Common.clamp(0 if (self.m_totalScore < (self.m_rate[Common.RATE_BASE] / 6)) else (self.m_totalScore * 10 / self.m_rate[Common.RATE_BASE]),0,10)
		self.m_curPointEnergy = 0
		self.m_energyStorage = self.m_agent.GetProperty("Hunger").m_energyStorage
		self.m_activityEffect = 0
		self.K_COLUMN_NAME = ["ENERGI", "Energy Storage","Tingkat Energi Terkini", "Laju Energi", "Efek Aktivitas", "Pengaruh Emosi", "Kalkulasi krn Efek Akt. dan Emosi", "Kalkulasi krn Efek Makan", "Total Energi 1 jam berikutnya", "Konversi Kalori ke Poin"]
	
	def CalculateScore(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		self.m_energyStorage = self.m_agent.GetProperty("Hunger").m_energyStorage
		self.m_curPointEnergy = self.m_energyStorage + self.m_pointEnergy
		self.m_currentScore = self.m_energyStorage# + self.m_totalScore
		self.m_activityEffect = self.m_agent.m_weight * self.m_agent.GetActivityEffect(self.m_type)
		self.m_scoreActAndEmo = self.m_currentScore - (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_activityEffect
		self.m_eatEffect = self.m_agent.GetProperty("Hunger").m_constraintEffectScore
		self.m_totalScore = self.m_scoreActAndEmo + self.m_eatEffect + self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
		
		self.m_totalScore = min(self.m_totalScore,self.m_rate[Common.RATE_BASE])
		self.m_pointEnergy = Common.clamp(self.m_totalScore * 10 / self.m_rate[Common.RATE_BASE],0,10)
	
	def PostUpdateActivityCalculation(self):
		pass
	
	def GetScore(self):
		return self.m_pointEnergy
	
	def PrintProperty(self):
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_scoreActAndEmo)+" "+Fmt(self.m_eatEffect)+" "+Fmt(self.m_totalScore)+" "+Fmt(self.m_pointEnergy)+"\n")
	
	def GetCalcParam(self):
		return [Fmt(self.m_energyStorage), Fmt(self.m_currentScore), Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]), Fmt(self.m_agent.GetActivityEffect(self.m_type)), Fmt(self.m_agent.GetEmotionalFactor()), Fmt(self.m_scoreActAndEmo), Fmt(self.m_eatEffect), Fmt(self.m_totalScore), Fmt(self.m_pointEnergy)]
	
	# def ProcessOutput(self):
		# return [Global.g_timer.GetFormattedHour(), 

class Exhausted(BioProperty):
	def __init__(self, agent, type, rate, current):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_totalScore = current
		self.m_scoreActAndEmo = 0
		self.m_specialEffect = 0
	
	def CalculateScore(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		self.m_currentScore = self.m_totalScore
		self.m_scoreActAndEmo = self.m_currentScore + (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type)
		self.m_specialEffect = 10 - ((self.m_scoreActAndEmo + self.m_agent.GetProperty("Energy").m_pointEnergy) / 2)
		self.m_totalScore = self.m_specialEffect + self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
		self.K_COLUMN_NAME = ["KELELAHAN", "Tingkat Kelelahan Terkini", "Laju Kelelahan", "Efek Aktivitas", "Pengaruh Emosi", "Kalkulasi krn Efek Akt. dan Emosi","Kalkulasi efek khusus", "Total Kelelahan 1 jam berikutnya"]
		self.m_totalScore = Common.clamp(self.m_totalScore,0,10)
		
	def PostUpdateActivityCalculation(self):
		pass
	
	def GetScore(self):
		return self.m_totalScore
	
	def PrintProperty(self):
		Global.Logger.LogDebug("Exhausted"+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE])+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_scoreActAndEmo)+" "+Fmt(self.m_specialEffect)+" "+Fmt(self.m_totalScore)+"\n")
	
	def GetCalcParam(self):
		return [Fmt(self.m_currentScore), Fmt(self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]), Fmt(self.m_agent.GetActivityEffect(self.m_type)), Fmt(self.m_agent.GetEmotionalFactor()), Fmt(self.m_scoreActAndEmo), Fmt(self.m_specialEffect), Fmt(self.m_totalScore)]
	
	# def ProcessOutput(self):
		# return [Global.g_timer.GetFormattedHour(), 
	
class Sleepy(BioProperty):
	def __init__(self, agent, type, rate, current, habit):
		BioProperty.__init__(self, agent, type, rate, current)
		self.m_habit = habit
		self.m_scoreActAndEmo = 0
		self.m_specialEffect = 0
		self.m_totalScore = current
		self.m_relatedActivityId = "B04"
		self.m_curRate = 0
		self.m_constraint = current
		self.K_COLUMN_NAME = ["KANTUK", "Tingkat Kantuk Terkini", "Laju Kantuk ", "Efek Aktivitas", "Pengaruh Emosi", "Kalkulasi krn Efek Akt. dan Emosi", "Kalkulasi efek khusus", "Total Kantuk 1 jam berikutnya", "Kebiasaan Tidur/Bangun", "Constraint", "Tidur/Bangun"]
	
	def CalculateScore(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		self.m_currentScore = self.m_constraint
		self.m_scoreActAndEmo = self.m_currentScore + (self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE] * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type)
		self.m_specialEffect = self.m_scoreActAndEmo + (self.m_agent.GetProperty("Exhausted").m_currentScore / (24 * Timer.MINUTE_IN_HOUR))
		self.m_curRate = self.m_rate[Common.AGENT_ASLEEP if self.m_agent.IsAsleep() else Common.AGENT_AWAKE]
		self.m_totalScore = self.m_specialEffect + self.m_curRate
		
		self.m_totalScore = Common.clamp(self.m_totalScore,0,10)
		randVal = (random.random() * 2) + 1
		isNoon = Global.g_timer.GetHour() > 8 and Global.g_timer.GetHour() < 17
		
		# self.m_constraint = self.m_totalScore + (((( -randVal if self.m_totalScore > 2 else -1) if self.IsHabit(Common.AGENT_AWAKE,Global.g_timer.GetHour()) else randVal)if self.m_agent.IsAsleep() else (randVal if (self.m_totalScore < 8 and self.IsHabit(Common.AGENT_ASLEEP,Global.g_timer.GetHour())) else 0)) / Timer.MINUTE_IN_HOUR)
		
		self.m_constraint = self.m_totalScore + ( ( ( ( (-6) if self.m_totalScore > 4 else (-2)) if isNoon else ( (-3) if self.m_totalScore > 2 else (-1))) if self.IsHabit(Common.AGENT_AWAKE,Global.g_timer.GetHour()) else (1) ) if self.m_agent.IsAsleep() else ( ( ( (4) if self.m_totalScore < 8 else ( (10 - self.m_totalScore) if self.m_totalScore > 10 else (0) ) ) if isNoon else ((2) if self.m_totalScore < 8 else ( (10 - self.m_totalScore) if self.m_totalScore > 10 else (0) )) ) if self.IsHabit(Common.AGENT_ASLEEP,Global.g_timer.GetHour()) else (0)) )
		
		if ((self.m_constraint >= 10 and self.IsHabit(Common.AGENT_ASLEEP,Global.g_timer.GetHour())) or (self.IsHabit(Common.AGENT_ASLEEP,Global.g_timer.GetHour()) and self.m_constraint >= 8)) and self.m_relatedActivity == None:
			self.TryTriggerRelatedActivity()
	
	def IsHabit(self, index, time):
		return self.m_habit[index][time]
		
	def PostUpdateActivityCalculation(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		Global.Logger.LogDebug("Post update "+Global.g_timer.GetFormattedHour()+" "+str(self.m_relatedActivity != None)+" "+str(self.m_constraint)+" "+str(self.IsHabit(Common.AGENT_AWAKE,Global.g_timer.GetHour()))+"\n")
		self.PrintProperty()
		if self.m_relatedActivity != None and ((self.m_constraint <= 0) or (self.IsHabit(Common.AGENT_AWAKE,Global.g_timer.GetHour()) and self.m_constraint <= 2)):
			if self.m_relatedActivity.m_next == "-" or not (self.m_relatedActivity.m_next in self.m_agent.m_nonIndependentAct):
				Global.Logger.LogDebug("Forcestop\n")
				Global.Logger.LogDebug(str(self.m_agent.m_nonIndependentAct)+"\n")
				self.m_relatedActivity.ForceStop()
		pass
	
	def GetScore(self):
		return self.m_totalScore
	
	def PrintProperty(self):
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_currentScore)+" "+Fmt(self.m_curRate)+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_scoreActAndEmo)+" "+Fmt(self.m_specialEffect)+" "+Fmt(self.m_totalScore) + " "+ ("KT" if self.IsHabit(Common.AGENT_ASLEEP,Global.g_timer.GetHour()) else ("KB" if self.IsHabit(Common.AGENT_AWAKE,Global.g_timer.GetHour()) else "-"))+" "+("T" if self.m_agent.IsAsleep() else "B")+"\n")
	
	def GetCalcParam(self):
		return [Fmt(self.m_currentScore), Fmt(self.m_curRate), Fmt(self.m_agent.GetActivityEffect(self.m_type)), Fmt(self.m_agent.GetEmotionalFactor()), Fmt(self.m_scoreActAndEmo), Fmt(self.m_specialEffect), Fmt(self.m_totalScore), ("KT" if self.IsHabit(Common.AGENT_ASLEEP,Timer.GetInstance().GetHour()) else ("KB" if self.IsHabit(Common.AGENT_AWAKE,Timer.GetInstance().GetHour()) else "-")),Fmt(self.m_constraint), ("T" if self.m_agent.IsAsleep() else "B")]
	
	# def ProcessOutput(self):
		# return [Global.g_timer.GetFormattedHour(), 

class Defecate(BioProperty):
	def __init__(self, agent, type, habit,  inStomach, curPressure, threshold, constant):
		BioProperty.__init__(self, agent, type, None, 0)
		self.m_habit = habit
		self.m_inStomach = inStomach
		# self.m_clepPressure = clepPressure
		self.m_inColon = 0
		self.m_rateStomachToIntestine = inStomach/(6 * Timer.MINUTE_IN_HOUR)
		self.m_inIntestine = self.m_rateStomachToIntestine / 12
		self.m_tick = 0
		self.m_tickStart = False
		self.m_inColonEdge = 0
		self.m_gotoRectum = 0
		self.m_eatEffect = 0
		self.m_rateIntestineToColon = 0
		self.m_agent = agent
		self.K_COLUMN_NAME = ["DEFEKASI", "Efek Makan", "Ada di Lambung", "Laju Lambung ke Usus Halus", "Ada di Usus Halus", "Laju dari Usus Halus ke Kolon", "Ada di Kolon", "Ada di ujung Kolon", "Laju dari Kolon ke Rektum", "Kebiasaan", "Efek Aktivitas", "Pengaruh Emosi", "Ada di Akhir Kolon Menuju Rektum", "Tingkat Tekanan Terkini", "Efek Defekasi", "BAB atau Tidak", "Konversi mmhg ke poin"]
		self.m_effectRemainingTime = 0
		self.K_SIX_HOUR = (6 * Timer.MINUTE_IN_HOUR)
		self.m_prevIntestine = 0
		self.m_toRectum = 0
		self.m_score = curPressure
		self.m_scorePoint = 0
		self.m_threshold = threshold
		self.m_constant = constant
		self.m_relatedActivityId = "B06"
	
	def CalculateScore(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		self.m_eatEffect = self.m_agent.GetProperty("Hunger").m_constraintEffectScore
		if self.m_eatEffect > 0:
			self.m_rateStomachToIntestine = (self.m_eatEffect + self.m_inStomach) / ((self.K_SIX_HOUR * 2) if self.m_agent.IsAsleep() else self.K_SIX_HOUR)
			#self.m_tickStart = True
		self.m_inStomach = max(self.m_inStomach + self.m_eatEffect - self.m_rateStomachToIntestine ,0)
		if self.m_inStomach == 0:
			self.m_rateStomachToIntestine = 0
		self.m_prevIntestine = self.m_inIntestine
		self.m_inIntestine += (self.m_rateStomachToIntestine / ((self.K_SIX_HOUR * 2) if self.m_agent.IsAsleep() else self.K_SIX_HOUR)) if self.m_inStomach >= 0 else (-self.m_rateIntestineToColon)
		self.m_inIntestine = max(0,self.m_inIntestine)
		# self.m_inIntestine += (self.m_rateStomachToIntestine - (self.m_rateIntestineToColon if self.m_tick >= self.K_SIX_HOUR else 0)) if self.m_inStomach > 0 else -(self.m_rateIntestineToColon if self.m_tick >= self.K_SIX_HOUR else 0)
		# self.m_inIntestine += (self.m_rateStomachToIntestine  - self.m_rateIntestineToColon)
	
		# if self.m_eatEffect > 0:
		# if self.m_inIntestine == 0:
			# self.m_rateIntestineToColon = 0
		# else:
		self.m_rateIntestineToColon = ((self.m_prevIntestine + self.m_eatEffect) / ((6 * 2) if self.m_agent.IsAsleep() else 6)) if self.m_eatEffect > 0 else (self.m_rateIntestineToColon if self.m_inIntestine > 0 else 0 )
		
		self.m_inColon = (self.m_inColonEdge - (self.m_rateToRectum * 3)) if (self.m_relatedActivity != None and self.m_relatedActivity.IsRunning()) else ((self.m_inColonEdge + self.m_rateIntestineToColon) if (self.m_inIntestine > 1) else (0 if self.m_inColonEdge <= 1 else self.m_rateToRectum))
		# self.m_inColon = (self.m_inColonEdge - ((self.m_rateToRectum if self.IsHabit(Timer.GetInstance().GetHourForTime(Timer.GetInstance().m_time - 1)) else 453.592) * 5 / self.m_relatedActivity.m_duration)) if (self.m_relatedActivity != None) else ((self.m_inColonEdge + self.m_rateIntestineToColon) if (self.m_inIntestine > 0) else ((self.m_inColonEdge - self.m_rateToRectum) if self.m_inColonEdge > 0 else 0))
		# self.m_inColonEdge = (self.m_inColon + (self.m_rateIntestineToColon / 24)) if self.m_agent.m_wasAsleep else (self.m_inColon + (self.m_rateIntestineToColon / 12) - (0 if (self.m_relatedActivity == None) else (453.592 / self.m_relatedActivity.m_duration)))
		self.m_inColonEdge = (self.m_inColon + (self.m_rateIntestineToColon / 24)) if self.m_agent.m_wasAsleep else (((self.m_inColon * (1 - (self.m_relatedActivity.m_runningTime / self.m_relatedActivity.m_duration))) + (self.m_rateIntestineToColon / 12)) if (self.m_relatedActivity != None  and self.m_relatedActivity.IsRunning()) else (self.m_inColon + (self.m_rateIntestineToColon / 12)))
		
		self.m_rateToRectum = self.m_inColonEdge * 0.1
		self.m_toRectum = (self.m_rateToRectum / 24) + (self.m_agent.GetActivityEffect(self.m_type) * self.m_agent.GetEmotionalFactor())
		
		# calc1 = (self.m_score / 8 + self.m_clepPressure + self.m_agent.GetActivityEffect(self.m_type)) * self.m_agent.GetEmotionalFactor()
		
		self.m_score = self.m_toRectum if (self.IsHabit(Global.g_timer.GetHour()) and (self.m_relatedActivity == None or not self.m_relatedActivity.IsRunning()) and self.m_toRectum < self.m_constant) else (self.m_toRectum * 0.7355)
		
		
		# self.m_score = (self.m_clepPressure * self.m_agent.GetEmotionalFactor() )if (self.m_agent.m_wasAsleep) else ((self.m_score / 12 + self.m_clepPressure + self.m_agent.GetActivityEffect(self.m_type))if (self.m_relatedActivity == None) else ((calc1 - ((27.539 if calc1 >= 23.955 else 23.955)/self.m_relatedActivity.m_duration)) if self.IsHabit(Timer.GetInstance().GetHourForTime(Timer.GetInstance().m_time - 1)) else (calc1 - ((31.143 if calc1 >= 28.747 else 28.747)/self.m_relatedActivity.m_duration))))
		# self.m_clepPressure = (self.m_toRectum * 0.7355)
		
		self.m_score = max(0,self.m_score)
		
		self.m_scorePoint = self.m_score * 10 / 28.747
		
	def GetScore(self):
		return self.m_scorePoint
		
	def PostUpdateActivityCalculation(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		if (not self.m_agent.IsAsleep()):
			if (self.m_relatedActivity == None) and (self.m_score > (23.955 if self.IsHabit(Global.g_timer.GetHour()) else 28.747)):
				self.TryTriggerRelatedActivity()
	
	def IsHabit(self, time):
		if self.m_habit == None:
			return False
		return self.m_habit[time]
	
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_eatEffect)+" "+Fmt(self.m_inStomach)+" "+Fmt(self.m_rateStomachToIntestine)+" "+Fmt(self.m_inIntestine)+" "+Fmt(self.m_rateIntestineToColon)+" "+Fmt(self.m_inColon)+" "+Fmt(self.m_inColonEdge)+" "+Fmt(self.m_rateToRectum)+" "+("K" if self.IsHabit(Global.g_timer.GetHour()) else "-")+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_toRectum)+" "+Fmt(self.m_clepPressure)+" "+Fmt(self.m_score)+" "+ ("B" if self.m_relatedActivity != None else "T")+" "+Fmt(self.m_scorePoint)+"\n")
	
	def GetCalcParam(self):
		return [Fmt(self.m_eatEffect), Fmt(self.m_inStomach), Fmt(self.m_rateStomachToIntestine), Fmt(self.m_inIntestine), Fmt(self.m_rateIntestineToColon), Fmt(self.m_inColon), Fmt(self.m_inColonEdge), Fmt(self.m_rateToRectum), ("K" if self.IsHabit(Timer.GetInstance().GetHour()) else "-"), Fmt(self.m_agent.GetActivityEffect(self.m_type)), Fmt(self.m_agent.GetEmotionalFactor()), Fmt(self.m_toRectum), Fmt(self.m_score), Fmt(self.m_score / self.m_relatedActivity.m_duration if self.m_relatedActivity != None else 0), ("B" if self.m_relatedActivity != None else "T"), Fmt(self.m_scorePoint)]
	
	# def ProcessOutput(self):
		# return [Global.g_timer.GetFormattedHour(), 

class Urinate(BioProperty):
	def __init__(self, agent, type, rate, effect, bodyWater, inBladder, remainingInBladder):
		BioProperty.__init__(self, agent, type, rate, 0)
		self.m_type = type
		self.m_rate /= Timer.MINUTE_IN_HOUR
		self.m_effect = effect
		self.m_bodyWater = bodyWater
		self.m_inBladder = inBladder
		self.m_remainingInBladder = remainingInBladder
		self.m_eatEffect = 0
		self.m_drinkEffect = 0
		self.m_relatedActivityId = "B05"
		self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_VALUE]# /= self.m_agent.GetActivityById(self.m_relatedActivityId).m_duration
		#self.m_effect[Common.EFFECT_URINATE_DEFECATE][Common.EFFECT_NEW_VALUE] /= self.m_agent.GetActivityById(self.m_agent.GetProperty("Defecate").m_relatedActivityId).m_duration
		self.m_point = self.m_inBladder / self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT] * 10
		self.m_urinateVol = 0
		self.K_COLUMN_NAME = ["URINASI", "Efek Minum 20% sampai di kemih (mL)", "Efek Makan 5% sampai di kemih (mL)", "Total Body Water", "Laju Kemih ", "Efek Aktivitas", "Pengaruh Emosi", "Ada di Kemih", "Volume Urine sekali BAK", "Sisa di Kemih", "Konversi mL ke Poin"]
	
	def CalculateScore(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		self.m_drinkEffect = self.m_agent.GetProperty("Thirst").m_mlUrinate * 0.2
		self.m_eatEffect = self.m_agent.GetProperty("Hunger").m_mlUrinate * 0.05
		self.m_bodyWater += self.m_drinkEffect + self.m_eatEffect - self.m_rate
		
		self.m_inBladder = self.m_inBladder - self.m_urinateVol + (self.m_rate * self.m_agent.GetEmotionalFactor()) + self.m_agent.GetActivityEffect(self.m_type) + (0 if self.m_agent.GetProperty("Defecate").m_relatedActivity == None or not self.m_agent.GetProperty("Defecate").m_relatedActivity.IsRunning() else self.m_rate)
		
		if self.m_inBladder > self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT] and self.m_relatedActivity == None:
			self.TryTriggerRelatedActivity()
		# if Global.g_timer.m_format == Common.FORMAT_TIME_MINUTE and self.m_inBladder > 10 and not self.m_effectStarted:
			# self.m_effectStarted = True
			# self.m_effectRemainingTime = self.m_duration
	def PostUpdateActivityCalculation(self):
		if self.m_agent.m_currentActivity!= None and self.m_agent.m_currentActivity.m_outdoor:
			return
		if self.m_relatedActivity != None and self.m_relatedActivity.IsRunning() and self.m_urinateVol == 0:
			self.m_urinateVol = (self.m_inBladder - self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_VALUE]) / self.m_relatedActivity.m_duration
		
		if self.m_relatedActivity == None or not self.m_relatedActivity.IsRunning() :
			self.m_urinateVol = 0
		
		# if self.m_relatedActivity != None or (self.m_agent.GetProperty("Defecate").m_relatedActivity != None and self.m_inBladder > self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT]):
			# self.m_remainingInBladder = self.m_inBladder - self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_VALUE]
		# elif self.m_agent.GetProperty("Defecate").m_relatedActivity != None or self.m_agent.GetProperty("Dirty").m_relatedActivity != None:
			# self.m_remainingInBladder = self.m_inBladder - self.m_effect[Common.EFFECT_URINATE_DEFECATE][Common.EFFECT_NEW_VALUE]
		# else:
			# self.m_remainingInBladder = self.m_inBladder
		
		self.m_remainingInBladder = self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_VALUE]
		self.m_point = self.m_inBladder / self.m_effect[Common.EFFECT_URINATE_NORMAL][Common.EFFECT_NEW_LIMIT] * 10
	
	def GetScore(self):
		return self.m_point
	
	def PrintProperty(self):
		# pass
		Global.Logger.LogDebug(self.m_type+" "+Fmt(self.m_drinkEffect)+" "+Fmt(self.m_eatEffect)+" "+Fmt(self.m_bodyWater)+" "+Fmt(self.m_rate)+" "+Fmt(self.m_agent.GetActivityEffect(self.m_type))+" "+Fmt(self.m_agent.GetEmotionalFactor())+" "+Fmt(self.m_inBladder)+" "+Fmt(self.m_remainingInBladder)+" "+Fmt(self.m_point)+"\n")
	
	def GetCalcParam(self):
		return [Fmt(self.m_drinkEffect), Fmt(self.m_eatEffect), Fmt(self.m_bodyWater), Fmt(self.m_rate), Fmt(self.m_agent.GetActivityEffect(self.m_type)), Fmt(self.m_agent.GetEmotionalFactor()), Fmt(self.m_inBladder), Fmt(self.m_urinateVol), Fmt(self.m_remainingInBladder), Fmt(self.m_point)]
	
	# def ProcessOutput(self):
		# return [Global.g_timer.GetFormattedHour(), 