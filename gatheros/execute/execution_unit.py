

from pprint import pprint
import sys



class ExecutionUnit :


	info = {'OS':'Linux'}

	def __init__ ( self, execute_command, commStruct ) :
		self.execute_command = execute_command
		self.commStruct = commStruct
		self.dependencies_met = set()
		self.allCommands = set( self.commStruct['Commands'].keys() ) 
		self.allCommandsDict = self.commStruct['Commands']
		
		self.notExecuted = self.allCommands


	def getLastResponseCode( self ) :
		os = self.info['OS']
		comm = 'echo $?'
		if os.lower().startswith('win') :
			comm = '$LastExitCode'				# powershell
			# comm = '%errorlevel%'				# prompt
		resp = self.executeAdhoc ( comm ).strip()
		resp = int(resp)
		return resp


	def executeCommandSet( self, commSet ) :

		commFailed = set()

		for comm_id in commSet :
			command = self.commStruct['Commands'][comm_id]
			self.notExecuted.remove( comm_id )

			try :
				response = self.execute_command ( command['command'] ).decode( 'utf8' )
				self.dependencies_met.update( command['unlocks'] )
				if 'tag' in command :
					self.info[ command['tag'] ] = 'response'

				try :
					response_code = self.getLastResponseCode ( )
					if response_code != 0 :
						print response_code, command['command']
					command['response_code'] = response_code
				except :
					print sys.exc_info()[0], sys.exc_info()[1]
					print "Couldn't get Response code for %s" % comm_id
					pass

			except :
				commFailed.add( comm_id )
				print sys.exc_info()[0], sys.exc_info()[1]
				print "[!] Command '%s' couldn't be executed." % comm_id
				print "'%s'" % command['command']
				# command['error'] = True
				print sys.exc_info()[0]
				continue


			try :
				filter_ = command['response_filter']
				if filter_ :
					response = self.filterResponse( response, filter_ )
			except KeyError:
				pass
			except :
				print "Command '%s' filter:\n>>> %s\n Couldn't be executed.\n" % (comm_id, filter_)
			command['response'] = response

		# commSet.difference_update( commFailed )
		return commSet


	def filterResponse( self, response, filter_ ) :
		ret = str( eval ( filter_,  ) )
		return ret


	def getReadyCommands( self ) :
		ret = set()
		for comm_id in self.notExecuted :
			command = self.allCommandsDict[ comm_id ]
			commDependencies = set( command['depends'] )
			if commDependencies <= self.dependencies_met :
				ret.add( comm_id )
		return ret


	def execute( self ) :
		wDependencies = set( [ id_ for id_, command in self.allCommandsDict.iteritems()\
										if command['depends'] ] )
		woutDependencies = self.allCommands - wDependencies

		readyCommands = self.getReadyCommands()

		print "Remaining Commands: %d" % len(self.notExecuted)
		while readyCommands :
			self.executeCommandSet( readyCommands )
			print "Remaining Commands: %d" % len(self.notExecuted)
			readyCommands = self.getReadyCommands()

		self.commStruct['Populated'] = True
		return self.commStruct



	def executeAdhoc( self, command ) :
		response = self.execute_command ( command ).decode( 'utf8' )
		return response